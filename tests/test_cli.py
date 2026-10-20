import json

from saemphysics.cli import main


def test_cli_runs_and_serializes_a_verified_request(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "operation": "differentiate",
                "question_id": "cli-derivative",
                "expression": "x**3",
            }
        ),
        encoding="utf-8",
    )

    assert main(["run", str(request_path)]) == 0

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert captured.err == ""
    assert result["question_id"] == "cli-derivative"
    assert result["result"]["derivative"] == "3*x**2"
    assert result["verification"]["status"] == "passed"
    assert [event["layer"] for event in result["trace"]] == [
        "semantic_ir",
        "execution_ir",
        "machine_ir",
        "runtime",
        "verification",
    ]


def test_cli_reports_invalid_request_without_success_output(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    request_path.write_text('{"operation":"unknown","question_id":"bad"}', encoding="utf-8")

    assert main(["run", str(request_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "saemphysics:" in captured.err


def test_cli_validates_canonical_question_record(tmp_path, capsys):
    question_path = tmp_path / "question.json"
    question_path.write_text(
        json.dumps(
            {
                "question_id": "synthetic-demo-001",
                "exam": "SaemPhysics synthetic demo",
                "year": 2026,
                "subject": "physics",
                "topic": "mechanics",
                "source": {
                    "document_id": "saemphysics-synthetic-demo",
                    "rights_status": "original",
                },
                "question_text": (
                    "A cart moves at 3 m/s and accelerates at 2 m/s^2 "
                    "for 4 s. Find its displacement."
                ),
            }
        ),
        encoding="utf-8",
    )

    assert main(["validate-question", str(question_path)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "valid": True,
        "question_id": "synthetic-demo-001",
        "rights_status": "original",
        "solution_status": "not_solved",
        "human_verified": False,
    }


def test_cli_rejects_question_without_source_provenance(tmp_path, capsys):
    question_path = tmp_path / "question.json"
    question_path.write_text(
        json.dumps(
            {
                "question_id": "missing-source",
                "exam": "Unknown",
                "year": 2026,
                "subject": "physics",
                "topic": "mechanics",
                "question_text": "A synthetic test question.",
            }
        ),
        encoding="utf-8",
    )

    assert main(["validate-question", str(question_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "source" in captured.err


def test_cli_interactive_interface_routes_student_request(tmp_path, capsys):
    request_path = tmp_path / "student-request.json"
    request_path.write_text(
        json.dumps(
            {
                "intent": "solve",
                "calculation": {
                    "operation": "differentiate",
                    "question_id": "cli-student",
                    "expression": "x**2",
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(["interact", str(request_path)]) == 0

    captured = capsys.readouterr()
    response = json.loads(captured.out)
    assert captured.err == ""
    assert response["intent"] == "solve"
    assert response["status"] == "completed"
    assert response["artifact"]["result"]["derivative"] == "2*x"
    assert response["verification"]["status"] == "passed"


def test_cli_lists_corpus_questions_without_leaking_answer_keys(capsys):
    assert main(["list-questions"]) == 0

    captured = capsys.readouterr()
    response = json.loads(captured.out)
    assert captured.err == ""
    assert response["question_count"] == 5
    assert response["questions"][0]["question_id"] == (
        "synthetic-constant-acceleration-001"
    )
    assert "official_answer" not in response["questions"][0]


def test_cli_interacts_with_question_id_from_validated_corpus(tmp_path, capsys):
    request_path = tmp_path / "practice-request.json"
    request_path.write_text(
        json.dumps(
            {
                "intent": "practice",
                "question_id": "synthetic-constant-acceleration-001",
            }
        ),
        encoding="utf-8",
    )

    assert main(["interact", str(request_path)]) == 0

    captured = capsys.readouterr()
    response = json.loads(captured.out)
    assert captured.err == ""
    assert response["status"] == "ready"
    assert response["artifact"]["question_id"] == (
        "synthetic-constant-acceleration-001"
    )
    assert "official_answer" not in response["artifact"]


def test_cli_rejects_unknown_corpus_question_id(tmp_path, capsys):
    request_path = tmp_path / "practice-request.json"
    request_path.write_text(
        json.dumps({"intent": "practice", "question_id": "unknown-question"}),
        encoding="utf-8",
    )

    assert main(["interact", str(request_path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not found in the validated corpus" in captured.err


def test_cli_runs_a_test_and_grades_submitted_answers(tmp_path, capsys):
    start_path = tmp_path / "start-test.json"
    start_path.write_text(
        json.dumps(
            {
                "intent": "start_test",
                "question_ids": [
                    "synthetic-constant-acceleration-001",
                    "synthetic-constant-acceleration-002",
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["interact", str(start_path)]) == 0
    started = json.loads(capsys.readouterr().out)
    assert started["status"] == "ready"
    assert len(started["artifact"]["questions"]) == 2
    assert all(
        "official_answer" not in question
        for question in started["artifact"]["questions"]
    )

    submit_path = tmp_path / "submit-test.json"
    submit_path.write_text(
        json.dumps(
            {
                "intent": "submit_test",
                "question_ids": [
                    "synthetic-constant-acceleration-001",
                    "synthetic-constant-acceleration-002",
                ],
                "answers": {
                    "synthetic-constant-acceleration-001": "B",
                    "synthetic-constant-acceleration-002": "A",
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(["interact", str(submit_path)]) == 0
    graded = json.loads(capsys.readouterr().out)
    assert graded["status"] == "completed"
    assert graded["artifact"]["correct_count"] == 2
    assert graded["artifact"]["total"] == 2
    assert graded["artifact"]["percentage"] == 100
    assert all(
        result["worked_solution"] is None
        for result in graded["artifact"]["results"]
    )
    assert "named human review" in graded["next_action"]
