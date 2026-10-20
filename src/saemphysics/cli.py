import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from collections.abc import Sequence

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.concepts import load_concept_graph
from saemphysics.ir import SemanticIR, compile_request
from saemphysics.models import QuestionRecord
from saemphysics.runtime import execute_plan
from saemphysics.runtime import NativeBackendError
from saemphysics.sources import (
    SourceManifest,
    load_question_corpus,
    validate_source_files,
)
from saemphysics.webapp import serve


def _read_json_object(path: str) -> dict[str, object]:
    content = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("The JSON input must be an object")
    return payload


def _read_request(path: str) -> SemanticIR:
    return SemanticIR.model_validate(_read_json_object(path))


def _run_request(path: str) -> dict[str, object]:
    request = _read_request(path)
    result = execute_plan(compile_request(request))
    return {
        "question_id": result.question_id,
        "result": asdict(result.result),
        "verification": asdict(result.verification),
        "trace": [asdict(event) for event in result.trace],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="saemphysics")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="execute and verify a JSON request")
    run_parser.add_argument(
        "request",
        help="path to a Semantic IR JSON request, or - to read from stdin",
    )
    validate_parser = commands.add_parser(
        "validate-question",
        help="validate a canonical question record without changing it",
    )
    validate_parser.add_argument(
        "question",
        help="path to a question-record JSON file, or - to read from stdin",
    )
    sources_parser = commands.add_parser(
        "validate-sources",
        help="validate a source manifest and its local file references",
    )
    sources_parser.add_argument(
        "manifest",
        help="path to a source manifest JSON file",
    )
    sources_parser.add_argument(
        "--root",
        default=".",
        help="project root used to resolve manifest paths (default: current directory)",
    )
    corpus_parser = commands.add_parser(
        "validate-corpus",
        help="validate question records against sources and the concept graph",
    )
    corpus_parser.add_argument(
        "questions",
        help="directory containing canonical question JSON files",
    )
    corpus_parser.add_argument(
        "--manifest",
        default="data/sources.json",
        help="source manifest JSON path (default: data/sources.json)",
    )
    corpus_parser.add_argument(
        "--root",
        default=".",
        help="project root used to resolve paths (default: current directory)",
    )
    corpus_parser.add_argument(
        "--concepts",
        default="data/concepts.json",
        help="versioned concept graph (default: data/concepts.json)",
    )
    concept_parser = commands.add_parser(
        "validate-concepts",
        help="validate concept IDs, prerequisites, and acyclic graph structure",
    )
    concept_parser.add_argument(
        "concepts",
        nargs="?",
        default="data/concepts.json",
        help="concept graph JSON (default: data/concepts.json)",
    )
    interact_parser = commands.add_parser(
        "interact",
        help="route a student request through the central processing interface",
    )
    interact_parser.add_argument(
        "student_request",
        help="path to a student-request JSON file, or - to read from stdin",
    )
    interact_parser.add_argument(
        "--questions",
        default="data/questions",
        help="question directory for ID-based selection (default: data/questions)",
    )
    interact_parser.add_argument(
        "--manifest",
        default="data/sources.json",
        help="source manifest for ID-based selection",
    )
    interact_parser.add_argument(
        "--root",
        default=".",
        help="project root used to validate selected questions",
    )
    interact_parser.add_argument(
        "--concepts",
        default="data/concepts.json",
        help="versioned concept graph (default: data/concepts.json)",
    )
    interact_parser.add_argument(
        "--native-kinematics",
        help="opt in to the cross-checked C++ constant-acceleration executable",
    )
    list_parser = commands.add_parser(
        "list-questions",
        help="list selectable questions without exposing answer keys",
    )
    list_parser.add_argument(
        "--questions",
        default="data/questions",
        help="question directory (default: data/questions)",
    )
    list_parser.add_argument(
        "--manifest",
        default="data/sources.json",
        help="source manifest (default: data/sources.json)",
    )
    list_parser.add_argument(
        "--root",
        default=".",
        help="project root used to validate selected questions",
    )
    list_parser.add_argument(
        "--concepts",
        default="data/concepts.json",
        help="versioned concept graph (default: data/concepts.json)",
    )
    web_parser = commands.add_parser(
        "web",
        help="start the local browser-based SaemPhysics workbench",
    )
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8000)
    web_parser.add_argument(
        "--native-kinematics",
        help="opt in to the cross-checked C++ constant-acceleration executable",
    )
    args = parser.parse_args(argv)

    if args.command == "web":
        serve(
            args.host,
            args.port,
            native_kinematics_executable=args.native_kinematics,
        )
        return 0

    try:
        if args.command == "run":
            output = _run_request(args.request)
        elif args.command == "validate-question":
            question = QuestionRecord.model_validate(
                _read_json_object(args.question)
            )
            output = {
                "valid": True,
                "question_id": question.question_id,
                "rights_status": question.source.rights_status.value,
                "solution_status": question.solution.status.value,
                "human_verified": question.review.human_verified,
            }
        elif args.command == "validate-sources":
            manifest = SourceManifest.model_validate(
                _read_json_object(args.manifest)
            )
            validate_source_files(manifest, args.root)
            output = {
                "valid": True,
                "document_count": len(manifest.documents),
                "rights_review_required": sum(
                    document.rights_status.value == "review_required"
                    for document in manifest.documents
                ),
                "ingestion_status_counts": {
                    status: sum(
                        document.ingestion_status == status
                        for document in manifest.documents
                    )
                    for status in (
                        "catalogued",
                        "extraction_pending",
                        "extracted",
                        "human_reviewed",
                    )
                },
            }
        elif args.command == "validate-concepts":
            graph = load_concept_graph(args.concepts)
            output = {
                "valid": True,
                "schema_version": graph.schema_version,
                "concept_count": len(graph.concepts),
                "reviewed_count": sum(
                    concept.review.human_verified for concept in graph.concepts
                ),
                "concept_ids": sorted(
                    concept.concept_id for concept in graph.concepts
                ),
            }
        elif args.command == "validate-corpus":
            manifest = SourceManifest.model_validate(
                _read_json_object(args.manifest)
            )
            graph = load_concept_graph(args.concepts)
            questions = load_question_corpus(
                args.questions,
                manifest,
                args.root,
                graph,
            )
            output = {
                "valid": True,
                "question_count": len(questions),
                "question_ids": sorted(
                    question.question_id for question in questions
                ),
                "source_document_ids": sorted(
                    {question.source.document_id for question in questions}
                ),
                "all_unsolved": all(
                    question.solution.status.value == "not_solved"
                    for question in questions
                ),
            }
        else:
            if args.command == "list-questions":
                manifest = SourceManifest.model_validate(
                    _read_json_object(args.manifest)
                )
                graph = load_concept_graph(args.concepts)
                questions = load_question_corpus(
                    args.questions,
                    manifest,
                    args.root,
                    graph,
                )
                output = {
                    "question_count": len(questions),
                    "questions": [
                        {
                            "question_id": question.question_id,
                            "subject": question.subject,
                            "topic": question.topic,
                            "question_text": question.question_text,
                            "option_count": len(question.options),
                        }
                        for question in sorted(
                            questions, key=lambda question: question.question_id
                        )
                    ],
                }
            else:
                request = StudentRequest.model_validate(
                    _read_json_object(args.student_request)
                )
                resolver = None
                if (
                    request.question_id is not None or request.question_ids
                ) and request.question is None:
                    manifest = SourceManifest.model_validate(
                        _read_json_object(args.manifest)
                    )
                    graph = load_concept_graph(args.concepts)
                    questions = load_question_corpus(
                        args.questions,
                        manifest,
                        args.root,
                        graph,
                    )
                    question_by_id = {
                        question.question_id: question for question in questions
                    }

                    def resolve_question(question_id: str) -> QuestionRecord:
                        try:
                            return question_by_id[question_id]
                        except KeyError as error:
                            raise ValueError(
                                f"Question {question_id!r} was not found in the validated corpus"
                            ) from error

                    resolver = resolve_question
                output = process_student_request(
                    request,
                    question_resolver=resolver,
                    native_kinematics_executable=args.native_kinematics,
                ).model_dump(mode="json")
    except (NativeBackendError, OSError, ValueError) as error:
        print(f"saemphysics: {error}", file=sys.stderr)
        return 2

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
