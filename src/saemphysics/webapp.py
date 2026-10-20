from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from pydantic import ValidationError

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.concepts import load_concept_graph
from saemphysics.models import QuestionRecord
from saemphysics.sources import SourceManifest, load_question_corpus
from saemphysics.student_frontend import render_student_page
from saemphysics.teacher_frontend import render_teacher_page
from saemphysics.teacher_workflow import (
    TeacherLessonInput,
    create_teacher_lesson_draft,
)


_MAX_REQUEST_BYTES = 1_048_576
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/assets/student.css": ("student.css", "text/css; charset=utf-8"),
}


def _loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    project_root: str | Path | None = None,
) -> ThreadingHTTPServer:
    """Create a local-only workbench server with a validated question corpus."""
    if not _loopback_host(host):
        raise ValueError("The development web server may bind only to a loopback host")

    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    manifest_payload = json.loads(
        (root / "data/sources.json").read_text(encoding="utf-8")
    )
    manifest = SourceManifest.model_validate(manifest_payload)
    concept_graph = load_concept_graph(root / "data/concepts.json")
    questions = load_question_corpus(
        "data/questions",
        manifest,
        root,
        concept_graph,
    )
    question_by_id = {question.question_id: question for question in questions}
    web_root = root / "web"

    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "SaemPhysicsWorkbench/0.1"

        def _method_not_allowed(self) -> None:
            self.send_response(405)
            self.send_header("Allow", "GET, POST")
            body = json.dumps({"error": "Method not allowed"}).encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, status: int, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )

        def do_GET(self) -> None:
            if self.path == "/student":
                self._send_html(200, render_student_page(questions))
                return
            if self.path == "/teacher":
                self._send_html(200, render_teacher_page())
                return
            if self.path == "/api/health":
                self._send_json(200, {"status": "ok", "question_count": len(questions)})
                return
            if self.path == "/api/questions":
                self._send_json(
                    200,
                    {
                        "question_count": len(questions),
                        "questions": [
                            {
                                "question_id": question.question_id,
                                "exam": question.exam,
                                "year": question.year,
                                "subject": question.subject,
                                "topic": question.topic,
                                "question_text": question.question_text,
                                "concepts": question.concepts,
                                "options": [
                                    option.model_dump(mode="json")
                                    for option in question.options
                                ],
                            }
                            for question in sorted(
                                questions, key=lambda item: item.question_id
                            )
                        ],
                    },
                )
                return
            if self.path == "/api/concepts":
                self._send_json(
                    200,
                    {
                        "schema_version": concept_graph.schema_version,
                        "concept_count": len(concept_graph.concepts),
                        "concepts": [
                            concept.model_dump(mode="json")
                            for concept in sorted(
                                concept_graph.concepts,
                                key=lambda item: item.concept_id,
                            )
                        ],
                    },
                )
                return
            asset = _ASSETS.get(self.path)
            if asset is None:
                self._send_json(404, {"error": "Not found"})
                return
            filename, content_type = asset
            try:
                body = (web_root / filename).read_bytes()
            except OSError as error:
                self._send_json(500, {"error": f"Workbench asset unavailable: {error}"})
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path == "/teacher":
                self._handle_teacher_form()
                return
            if self.path == "/student":
                self._handle_student_form()
                return
            if self.path != "/api/interact":
                self._send_json(404, {"error": "Not found"})
                return
            if self.headers.get_content_type() != "application/json":
                self._send_json(415, {"error": "Content-Type must be application/json"})
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_json(411, {"error": "A valid Content-Length is required"})
                return
            if content_length < 0:
                self._send_json(400, {"error": "Content-Length cannot be negative"})
                return
            if content_length > _MAX_REQUEST_BYTES:
                self._send_json(413, {"error": "Request body exceeds the 1 MiB limit"})
                return
            try:
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("The interaction request must be a JSON object")
                request = StudentRequest.model_validate(payload)

                def resolve_question(question_id: str) -> QuestionRecord:
                    try:
                        return question_by_id[question_id]
                    except KeyError as error:
                        raise ValueError(
                            f"Question {question_id!r} was not found in the validated corpus"
                        ) from error

                response = process_student_request(
                    request,
                    question_resolver=resolve_question,
                )
            except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, ValueError) as error:
                self._send_json(400, {"error": str(error)})
                return
            self._send_json(200, response.model_dump(mode="json"))

        def _handle_teacher_form(self) -> None:
            if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self._send_html(
                    415,
                    render_teacher_page(
                        error="Form submissions must be URL encoded."
                    ),
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_html(
                    411,
                    render_teacher_page(error="A valid Content-Length is required."),
                )
                return
            if content_length < 0:
                self._send_html(
                    400,
                    render_teacher_page(error="Content-Length cannot be negative."),
                )
                return
            if content_length > _MAX_REQUEST_BYTES:
                self._send_html(
                    413,
                    render_teacher_page(error="The form exceeds the 1 MiB request limit."),
                )
                return

            try:
                form = parse_qs(
                    self.rfile.read(content_length).decode("utf-8"),
                    keep_blank_values=True,
                    strict_parsing=True,
                )
                expected_fields = {
                    "action",
                    "question_text",
                    "initial_velocity_m_s",
                    "acceleration_m_s2",
                    "time_s",
                    "intuition",
                    "common_misconception",
                }
                if set(form) != expected_fields:
                    raise ValueError("The form contains missing or unsupported fields.")

                def field(name: str) -> str:
                    values = form[name]
                    if len(values) != 1:
                        raise ValueError(f"Form field {name!r} must be submitted once.")
                    return values[0]

                if field("action") != "create_lesson":
                    raise ValueError("Unsupported teacher form action.")
                request = TeacherLessonInput(
                    question_text=field("question_text"),
                    initial_velocity_m_s=field("initial_velocity_m_s"),
                    acceleration_m_s2=field("acceleration_m_s2"),
                    time_s=field("time_s"),
                    intuition=field("intuition") or None,
                    common_misconception=field("common_misconception") or None,
                )
                response = create_teacher_lesson_draft(request)
            except (
                UnicodeDecodeError,
                ValidationError,
                ValueError,
            ) as error:
                self._send_html(
                    400,
                    render_teacher_page(error=str(error)),
                )
                return
            self._send_html(200, render_teacher_page(response=response))

        def _handle_student_form(self) -> None:
            if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self._send_html(
                    415,
                    render_student_page(
                        questions, error="Form submissions must be URL encoded."
                    ),
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_html(
                    411,
                    render_student_page(
                        questions, error="A valid Content-Length is required."
                    ),
                )
                return
            if content_length < 0:
                self._send_html(
                    400,
                    render_student_page(
                        questions, error="Content-Length cannot be negative."
                    ),
                )
                return
            if content_length > _MAX_REQUEST_BYTES:
                self._send_html(
                    413,
                    render_student_page(
                        questions, error="The form exceeds the 1 MiB request limit."
                    ),
                )
                return

            selected_question = None
            try:
                form = parse_qs(
                    self.rfile.read(content_length).decode("utf-8"),
                    keep_blank_values=True,
                    strict_parsing=True,
                )

                def field(name: str) -> str:
                    values = form.get(name, [])
                    if len(values) != 1 or not values[0]:
                        raise ValueError(f"Form field {name!r} must be submitted once.")
                    return values[0]

                action = field("action")
                question_id = field("question_id")
                expected_fields = {"action", "question_id"}
                if action == "submit_answer":
                    expected_fields.add("selected_option")
                if set(form) != expected_fields:
                    raise ValueError("The form contains unsupported fields.")
                selected_question = question_by_id.get(question_id)
                if selected_question is None:
                    raise ValueError(
                        f"Question {question_id!r} was not found in the validated corpus."
                    )
                if action == "practice":
                    request = StudentRequest(
                        intent="practice",
                        question_id=question_id,
                    )
                elif action == "submit_answer":
                    request = StudentRequest(
                        intent="submit_answer",
                        question_id=question_id,
                        selected_option=field("selected_option"),
                    )
                else:
                    raise ValueError("Unsupported student form action.")

                response = process_student_request(
                    request,
                    question_resolver=lambda requested_id: question_by_id[requested_id],
                )
            except (
                UnicodeDecodeError,
                ValueError,
                ValidationError,
            ) as error:
                self._send_html(
                    400,
                    render_student_page(
                        questions,
                        selected_question=selected_question,
                        error=str(error),
                    ),
                )
                return
            self._send_html(
                200,
                render_student_page(
                    questions,
                    selected_question=selected_question,
                    response=response,
                ),
            )

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def do_OPTIONS(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def log_message(self, format: str, *args: Any) -> None:
            super().log_message(format, *args)

    server = ThreadingHTTPServer((host, port), WorkbenchHandler)
    server.daemon_threads = True
    return server


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    project_root: str | Path | None = None,
) -> None:
    """Run the local development workbench until interrupted."""
    server = create_server(host, port, project_root)
    print(f"SaemPhysics workbench: http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SaemPhysics workbench.")
    finally:
        server.server_close()
