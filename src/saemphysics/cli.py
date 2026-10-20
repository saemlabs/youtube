import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from collections.abc import Sequence

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.ir import SemanticIR, compile_request
from saemphysics.models import QuestionRecord
from saemphysics.runtime import execute_plan


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
    interact_parser = commands.add_parser(
        "interact",
        help="route a student request through the central processing interface",
    )
    interact_parser.add_argument(
        "student_request",
        help="path to a student-request JSON file, or - to read from stdin",
    )
    args = parser.parse_args(argv)

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
        else:
            request = StudentRequest.model_validate(
                _read_json_object(args.student_request)
            )
            output = process_student_request(request).model_dump(mode="json")
    except (OSError, ValueError) as error:
        print(f"saemphysics: {error}", file=sys.stderr)
        return 2

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
