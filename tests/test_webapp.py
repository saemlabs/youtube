import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from saemphysics.webapp import create_server


@pytest.fixture
def workbench_server():
    server = create_server(port=0, project_root=Path.cwd())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.fixture
def workbench_server_factory():
    servers = []

    def start():
        server = create_server(port=0, project_root=Path.cwd())
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return f"http://127.0.0.1:{server.server_port}"

    yield start

    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get_json(base_url, path):
    with urlopen(f"{base_url}{path}", timeout=3) as response:
        return response.status, response.headers, json.loads(response.read())


def post_json(base_url, payload):
    request = Request(
        f"{base_url}/api/interact",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def post_form(base_url, fields, path="/student"):
    request = Request(
        f"{base_url}{path}",
        data=urlencode(fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8")


def test_server_serves_static_workbench_with_security_headers(workbench_server):
    with urlopen(workbench_server, timeout=3) as response:
        html = response.read().decode("utf-8")

    assert response.status == 200
    assert "SaemPhysics Workbench" in html
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_python_student_frontend_shows_teacher_profile_and_safe_question_picker(
    workbench_server,
):
    with urlopen(f"{workbench_server}/student", timeout=3) as response:
        page = response.read().decode("utf-8")

    assert response.status == 200
    assert "Python-rendered interface" in page
    assert 'href="https://www.youtube.com/@SaemPhysics"' in page
    assert "synthetic-constant-acceleration-001" in page
    assert "official_answer" not in page
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")


def test_student_frontend_exposes_shared_verified_math_capabilities(workbench_server):
    with urlopen(f"{workbench_server}/student", timeout=3) as response:
        page = response.read().decode("utf-8")
    with urlopen(f"{workbench_server}/assets/student.js", timeout=3) as response:
        script = response.read().decode("utf-8")

    assert "Solve and check a calculation" in page
    assert 'id="student-operation"' in page
    assert "solve_linear_system" in page
    assert 'src="/assets/student.js"' in page
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert 'fetch("/api/interact"' in script
    assert "verification?.checks" in script
    assert "response.trace" in script
    assert "innerHTML" not in script


@pytest.mark.parametrize(
    ("calculation", "expected_result"),
    [
        (
            {
                "operation": "solve_constant_acceleration",
                "initial_velocity_m_s": "3",
                "acceleration_m_s2": "2",
                "time_s": "4",
            },
            {
                "initial_velocity_m_s": "3",
                "acceleration_m_s2": "2",
                "time_s": "4",
                "displacement_m": "28",
                "final_velocity_m_s": "11",
            },
        ),
        (
            {"operation": "differentiate", "expression": "x**3"},
            {
                "expression": "x**3",
                "variable": "x",
                "derivative": "3*x**2",
                "checks": [
                    {
                        "name": "symbolic_derivative",
                        "passed": True,
                        "details": "Derivative residual: 0",
                    }
                ],
            },
        ),
        (
            {
                "operation": "definite_integral",
                "expression": "2 + 3*x",
                "lower_bound": "0",
                "upper_bound": "4",
            },
            None,
        ),
        (
            {
                "operation": "solve_linear_system",
                "coefficients": [["2", "1"], ["1", "-1"]],
                "right_hand_side": ["5", "1"],
            },
            {
                "solution": ["2", "1"],
                "determinant": "-3",
                "residuals": ["0", "0"],
                "checks": [
                    {
                        "name": "linear_system_residual",
                        "passed": True,
                        "details": "A*x - b = (0, 0)",
                    }
                ],
            },
        ),
    ],
)
def test_student_solver_api_returns_verified_results(
    workbench_server, calculation, expected_result
):
    status, response = post_json(
        workbench_server,
        {
            "intent": "solve",
            "calculation": {
                "question_id": "student-workbench-calculation",
                **calculation,
            },
        },
    )

    assert status == 200
    assert response["status"] == "completed"
    assert response["verification"]["status"] == "passed"
    assert all(check["passed"] for check in response["verification"]["checks"])
    result = response["artifact"]["result"]
    if calculation["operation"] == "definite_integral":
        assert result["value"] == "32"
    else:
        assert result == expected_result
    assert response["trace"][-1]["layer"] == "verification"


def test_product_page_is_a_prelaunch_catalog_by_default(workbench_server):
    with urlopen(f"{workbench_server}/products", timeout=3) as response:
        page = response.read().decode("utf-8")

    assert response.status == 200
    assert "Constant Acceleration Starter Notes" in page
    assert "₹99 one-time" in page
    assert "US$2.99 one-time" in page
    assert "checkout is not enabled yet" in page
    assert "href=\"https://www.youtube.com/@SaemPhysics\"" in page
    assert "Razorpay" not in page.split("Pre-launch preview")[0]


def test_product_page_uses_configured_hosted_payment_links(
    workbench_server_factory, monkeypatch
):
    monkeypatch.setenv("SAEMPHYSICS_SALES_ENABLED", "true")
    monkeypatch.setenv(
        "SAEMPHYSICS_RAZORPAY_PAYMENT_URL",
        "https://rzp.io/i/sample-notes",
    )
    monkeypatch.setenv(
        "SAEMPHYSICS_PAYPAL_PAYMENT_URL",
        "https://www.paypal.com/ncp/payment/sample-notes",
    )
    monkeypatch.setenv("SAEMPHYSICS_SELLER_NAME", "SaemPhysics")
    monkeypatch.setenv("SAEMPHYSICS_SUPPORT_EMAIL", "teacher@example.com")
    monkeypatch.setenv("SAEMPHYSICS_TERMS_URL", "https://saemphysics.example/terms")
    monkeypatch.setenv(
        "SAEMPHYSICS_PRIVACY_URL",
        "https://saemphysics.example/privacy",
    )
    monkeypatch.setenv(
        "SAEMPHYSICS_REFUNDS_URL",
        "https://saemphysics.example/refunds",
    )
    monkeypatch.setenv("SAEMPHYSICS_NOTES_REVIEWED", "true")
    base_url = workbench_server_factory()
    with urlopen(f"{base_url}/products", timeout=3) as response:
        page = response.read().decode("utf-8")
    assert response.status == 200
    assert 'href="https://rzp.io/i/sample-notes"' in page
    assert 'href="https://www.paypal.com/ncp/payment/sample-notes"' in page
    assert "SaemPhysics</p>" in page
    assert 'href="https://saemphysics.example/refunds"' in page
    assert 'rel="noopener noreferrer"' in page


@pytest.mark.parametrize(
    ("provider", "url"),
    [
        ("RAZORPAY", "https://evil.example/checkout"),
        ("PAYPAL", "http://www.paypal.com/ncp/payment/notes"),
        ("PAYPAL", "https://user@paypal.com/ncp/payment/notes"),
        ("RAZORPAY", "https://rzp.io/i/notes#fragment"),
    ],
)
def test_sales_enabled_rejects_untrusted_or_non_https_payment_links(
    workbench_server_factory, monkeypatch, provider, url
):
    monkeypatch.setenv("SAEMPHYSICS_SALES_ENABLED", "true")
    monkeypatch.setenv(
        "SAEMPHYSICS_RAZORPAY_PAYMENT_URL",
        "https://rzp.io/i/sample-notes",
    )
    monkeypatch.setenv(
        "SAEMPHYSICS_PAYPAL_PAYMENT_URL",
        "https://www.paypal.com/ncp/payment/sample-notes",
    )
    monkeypatch.setenv(f"SAEMPHYSICS_{provider}_PAYMENT_URL", url)

    with pytest.raises(ValueError, match="checkout URL is invalid"):
        create_server(port=0, project_root=Path.cwd())


def test_sales_enabled_requires_reviewed_content_and_policy_links(monkeypatch):
    monkeypatch.setenv("SAEMPHYSICS_SALES_ENABLED", "true")
    monkeypatch.setenv(
        "SAEMPHYSICS_RAZORPAY_PAYMENT_URL",
        "https://rzp.io/i/sample-notes",
    )
    monkeypatch.setenv(
        "SAEMPHYSICS_PAYPAL_PAYMENT_URL",
        "https://www.paypal.com/ncp/payment/sample-notes",
    )
    with pytest.raises(ValueError, match="HTTPS terms, privacy, and refund"):
        create_server(port=0, project_root=Path.cwd())


def test_python_student_frontend_uses_central_practice_and_grading_flow(workbench_server):
    question_id = "synthetic-constant-acceleration-001"
    status, page = post_form(
        workbench_server,
        {"action": "practice", "question_id": question_id},
    )

    assert status == 200
    assert "name=\"selected_option\"" in page
    assert "The answer key is withheld until submission." in page
    assert "correct_option" not in page

    status, page = post_form(
        workbench_server,
        {
            "action": "submit_answer",
            "question_id": question_id,
            "selected_option": "B",
        },
    )

    assert status == 200
    assert "Correct." in page
    assert "Answer after submission: <strong>B</strong>" in page
    assert "verified explanation is not" in page


def test_python_student_frontend_rejects_unknown_corpus_ids(workbench_server):
    status, page = post_form(
        workbench_server,
        {"action": "practice", "question_id": "not-in-corpus"},
    )

    assert status == 400
    assert "not found in the validated corpus" in page


def test_teacher_studio_builds_reviewable_lesson_with_exact_checks(workbench_server):
    with urlopen(f"{workbench_server}/teacher", timeout=3) as response:
        page = response.read().decode("utf-8")
    assert response.status == 200
    assert "Teacher lesson studio" in page
    assert 'name="question_text"' in page
    assert 'name="initial_velocity_m_s"' in page
    assert 'name="common_misconception"' in page

    status, page = post_form(
        workbench_server,
        {
            "action": "create_lesson",
            "question_text": (
                "A cart moves at 3 m/s and accelerates at 2 m/s^2 for 4 s. "
                "Find displacement and final velocity."
            ),
            "initial_velocity_m_s": "3",
            "acceleration_m_s2": "2",
            "time_s": "4",
            "intuition": "Velocity changes steadily during each second.",
            "common_misconception": "Confusing final velocity with displacement.",
        },
        path="/teacher",
    )

    assert status == 200
    assert "Lesson draft" in page
    assert "Displacement: s = ut + 1/2 at^2" in page
    assert "28 m" in page
    assert "11 m/s" in page
    assert "Execution trace" in page
    assert "semantic_ir" in page
    assert "Publication blockers" in page
    assert "A human reviewer has not approved the question." in page
    assert "Source rights are not cleared for publication." in page
    assert "not a finished or approved video" in page


def test_teacher_studio_rejects_invalid_math_and_escapes_teacher_text(
    workbench_server,
):
    fields = {
        "action": "create_lesson",
        "question_text": '<script>alert("lesson")</script> A cart accelerates.',
        "initial_velocity_m_s": "not-a-number",
        "acceleration_m_s2": "2",
        "time_s": "4",
        "intuition": "",
        "common_misconception": "",
    }
    status, page = post_form(workbench_server, fields, path="/teacher")


    assert status == 400
    assert "Semantic IR inputs must be exact rational numbers" in page
    assert "<script>alert" not in page

    fields["initial_velocity_m_s"] = "3"
    status, page = post_form(workbench_server, fields, path="/teacher")

    assert status == 200
    assert "&lt;script&gt;" in page
    assert "<script>alert" not in page


def test_teacher_studio_rejects_unknown_fields(workbench_server):
    status, page = post_form(
        workbench_server,
        {
            "action": "create_lesson",
            "question_text": "A cart accelerates for four seconds.",
            "initial_velocity_m_s": "3",
            "acceleration_m_s2": "2",
            "time_s": "4",
            "intuition": "",
            "common_misconception": "",
            "publish_now": "true",
        },
        path="/teacher",
    )

    assert status == 400
    assert "missing or unsupported fields" in page


def test_frontend_assets_are_served_from_fixed_routes(workbench_server):
    for path, expected_type in (
        ("/assets/app.css", "text/css"),
        ("/assets/app.js", "text/javascript"),
        ("/assets/student.css", "text/css"),
    ):
        with urlopen(f"{workbench_server}{path}", timeout=3) as response:
            asset = response.read()
            assert response.status == 200
            assert expected_type in response.headers["Content-Type"]
            assert asset


def test_question_endpoint_returns_safe_corpus_fields(workbench_server):
    status, headers, payload = get_json(workbench_server, "/api/questions")

    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    assert payload["question_count"] == 5
    first_question = payload["questions"][0]
    assert first_question["question_id"] == "synthetic-constant-acceleration-001"
    assert "official_answer" not in first_question
    assert "correct_option" not in first_question
    assert first_question["concepts"] == [
        "constant_acceleration",
        "displacement",
        "final_velocity",
    ]


def test_concept_endpoint_exposes_reviewable_graph_without_marking_it_approved(
    workbench_server,
):
    status, headers, payload = get_json(workbench_server, "/api/concepts")

    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    assert payload["schema_version"] == "1.0"
    assert payload["concept_count"] == 3
    assert all(not item["review"]["human_verified"] for item in payload["concepts"])
    displacement = next(
        item for item in payload["concepts"] if item["concept_id"] == "displacement"
    )
    assert displacement["prerequisites"] == ["constant_acceleration"]


def test_api_handles_verified_math_and_rejects_unknown_question(workbench_server):
    status, response = post_json(
        workbench_server,
        {
            "intent": "solve",
            "calculation": {
                "operation": "solve_constant_acceleration",
                "question_id": "web-motion",
                "initial_velocity_m_s": "3",
                "acceleration_m_s2": "2",
                "time_s": "4",
            },
        },
    )

    assert status == 200
    assert response["verification"]["status"] == "passed"
    assert response["artifact"]["result"]["displacement_m"] == "28"
    assert len(response["trace"]) == 5

    status, response = post_json(
        workbench_server,
        {"intent": "practice", "question_id": "not-in-corpus"},
    )
    assert status == 400
    assert "not found in the validated corpus" in response["error"]


def test_api_runs_test_without_revealing_keys_until_submission(workbench_server):
    ids = [
        "synthetic-constant-acceleration-001",
        "synthetic-constant-acceleration-002",
    ]
    status, started = post_json(
        workbench_server,
        {"intent": "start_test", "question_ids": ids},
    )

    assert status == 200
    assert all("official_answer" not in question for question in started["artifact"]["questions"])

    status, graded = post_json(
        workbench_server,
        {
            "intent": "submit_test",
            "question_ids": ids,
            "answers": {ids[0]: "B", ids[1]: "A"},
        },
    )
    assert status == 200
    assert graded["artifact"]["correct_count"] == 2
    assert all(
        result["worked_solution"] is None
        for result in graded["artifact"]["results"]
    )


def test_api_rejects_unsupported_routes_content_types_and_large_bodies(workbench_server):
    unsupported = Request(
        f"{workbench_server}/api/private",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(HTTPError) as route_error:
        urlopen(unsupported, timeout=3)
    assert route_error.value.code == 404

    wrong_type = Request(
        f"{workbench_server}/api/interact",
        data=b"{}",
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    with pytest.raises(HTTPError) as type_error:
        urlopen(wrong_type, timeout=3)
    assert type_error.value.code == 415

    oversized = Request(
        f"{workbench_server}/api/interact",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(1_048_577),
        },
        method="POST",
    )
    with pytest.raises(HTTPError) as size_error:
        urlopen(oversized, timeout=3)
    assert size_error.value.code == 413

    unsupported_method = Request(
        f"{workbench_server}/api/interact",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with pytest.raises(HTTPError) as method_error:
        urlopen(unsupported_method, timeout=3)
    assert method_error.value.code == 405
    assert method_error.value.headers["Allow"] == "GET, POST"


def test_workbench_refuses_non_loopback_binding():
    with pytest.raises(ValueError, match="loopback host"):
        create_server(host="0.0.0.0", port=8000)
