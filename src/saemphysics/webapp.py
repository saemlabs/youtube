from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.models import QuestionRecord
from saemphysics.sources import SourceManifest, load_question_corpus


_MAX_REQUEST_BYTES = 1_048_576
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
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
    questions = load_question_corpus("data/questions", manifest, root)
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
