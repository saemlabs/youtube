import json
from pathlib import Path
import shutil
import subprocess
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from saemphysics.central import StudentRequest, process_student_request
from saemphysics.cli import main
from saemphysics.runtime import NativeBackendError
from saemphysics.webapp import create_server


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native/cpp/constant_acceleration.cpp"
CONTRACT = ROOT / "contracts/v1/conformance.json"


def _contract_vectors():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def native_solver(tmp_path_factory):
    compiler = shutil.which("c++")
    if compiler is None:
        pytest.skip("A C++17 compiler is required for native conformance tests")
    executable = tmp_path_factory.mktemp("native-cpp") / "saemphysics-kinematics"
    subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(SOURCE),
            "-o",
            str(executable),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return executable


@pytest.fixture
def workbench_server_factory():
    servers = []

    def start(native_executable):
        server = create_server(
            port=0,
            project_root=ROOT,
            native_kinematics_executable=str(native_executable),
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return f"http://127.0.0.1:{server.server_port}"

    yield start

    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _post_motion_request(base_url):
    request = Request(
        f"{base_url}/api/interact",
        data=json.dumps(
            {
                "intent": "solve",
                "calculation": {
                    "operation": "solve_constant_acceleration",
                    "question_id": "native-web-motion",
                    "initial_velocity_m_s": "3",
                    "acceleration_m_s2": "2",
                    "time_s": "4",
                },
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def test_cpp_constant_acceleration_matches_all_shared_vectors(native_solver):
    vectors = _contract_vectors()["valid_vectors"]
    motion_vectors = [
        vector
        for vector in vectors
        if vector["request"]["calculation"]["operation"]
        == "solve_constant_acceleration"
    ]
    assert len(motion_vectors) == 2

    for vector in motion_vectors:
        calculation = vector["request"]["calculation"]
        result = subprocess.run(
            [
                str(native_solver),
                calculation["initial_velocity_m_s"],
                calculation["acceleration_m_s2"],
                calculation["time_s"],
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(result.stdout) == vector["expected"]["artifact"]["result"]


def test_cpp_native_capability_routes_through_central_processor(native_solver):
    vectors = _contract_vectors()["valid_vectors"]
    motion_vectors = [
        vector
        for vector in vectors
        if vector["request"]["calculation"]["operation"]
        == "solve_constant_acceleration"
    ]

    for vector in motion_vectors:
        response = process_student_request(
            StudentRequest.model_validate(vector["request"]),
            native_kinematics_executable=str(native_solver),
        )
        payload = response.model_dump(mode="json")

        assert payload["status"] == vector["expected"]["status"]
        assert payload["artifact"] == vector["expected"]["artifact"]
        assert payload["verification"]["status"] == "passed"
        assert payload["trace"][-2]["event"] == "cpp_native_cross_checked"
        assert "cross-checked" in payload["trace"][-2]["details"]


def test_cpp_native_capability_fails_closed_on_result_mismatch(tmp_path):
    wrong_backend = tmp_path / "wrong-native-backend"
    wrong_backend.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        "'{\"initial_velocity_m_s\":\"3\",\"acceleration_m_s2\":\"2\","
        "\"time_s\":\"4\",\"displacement_m\":\"999\","
        "\"final_velocity_m_s\":\"11\"}'\n",
        encoding="utf-8",
    )
    wrong_backend.chmod(0o755)
    request = StudentRequest.model_validate(
        {
            "intent": "solve",
            "calculation": {
                "operation": "solve_constant_acceleration",
                "question_id": "native-mismatch",
                "initial_velocity_m_s": "3",
                "acceleration_m_s2": "2",
                "time_s": "4",
            },
        }
    )

    with pytest.raises(NativeBackendError, match="does not match"):
        process_student_request(
            request,
            native_kinematics_executable=str(wrong_backend),
        )


def test_cpp_native_capability_is_available_through_cli(
    native_solver, tmp_path, capsys
):
    request_path = tmp_path / "motion-request.json"
    request_path.write_text(
        json.dumps(
            {
                "intent": "solve",
                "calculation": {
                    "operation": "solve_constant_acceleration",
                    "question_id": "native-cli-motion",
                    "initial_velocity_m_s": "3",
                    "acceleration_m_s2": "2",
                    "time_s": "4",
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(
        [
            "interact",
            str(request_path),
            "--native-kinematics",
            str(native_solver),
        ]
    ) == 0

    captured = capsys.readouterr()
    response = json.loads(captured.out)
    assert captured.err == ""
    assert response["artifact"]["result"]["displacement_m"] == "28"
    assert response["verification"]["status"] == "passed"
    assert response["trace"][-2]["event"] == "cpp_native_cross_checked"


def test_cpp_native_capability_is_available_through_web_api(
    native_solver, workbench_server_factory
):
    base_url = workbench_server_factory(native_solver)

    status, response = _post_motion_request(base_url)

    assert status == 200
    assert response["artifact"]["result"]["displacement_m"] == "28"
    assert response["verification"]["status"] == "passed"
    assert response["trace"][-2]["event"] == "cpp_native_cross_checked"


def test_web_api_returns_explicit_error_for_native_mismatch(
    tmp_path, workbench_server_factory
):
    wrong_backend = tmp_path / "wrong-native-backend"
    wrong_backend.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        "'{\"initial_velocity_m_s\":\"3\",\"acceleration_m_s2\":\"2\","
        "\"time_s\":\"4\",\"displacement_m\":\"999\","
        "\"final_velocity_m_s\":\"11\"}'\n",
        encoding="utf-8",
    )
    wrong_backend.chmod(0o755)
    base_url = workbench_server_factory(wrong_backend)

    status, response = _post_motion_request(base_url)

    assert status == 502
    assert "does not match" in response["error"]


def test_cpp_native_backend_rejects_non_motion_calculations(native_solver):
    request = StudentRequest.model_validate(
        {
            "intent": "solve",
            "calculation": {
                "operation": "differentiate",
                "question_id": "native-derivative",
                "expression": "x**2",
            },
        }
    )

    with pytest.raises(ValueError, match="supports only constant acceleration"):
        process_student_request(
            request,
            native_kinematics_executable=str(native_solver),
        )


def test_cpp_native_backend_rejects_non_solve_requests(native_solver):
    request = StudentRequest.model_validate(
        {
            "intent": "practice",
            "question_id": "not-needed-for-native-solve",
        }
    )

    with pytest.raises(ValueError, match="only for solve requests"):
        process_student_request(
            request,
            native_kinematics_executable=str(native_solver),
        )


@pytest.mark.parametrize(
    "vector",
    [
        vector
        for vector in _contract_vectors()["invalid_vectors"]
        if vector["request"].get("calculation", {}).get("operation")
        == "solve_constant_acceleration"
    ],
    ids=lambda vector: vector["id"],
)
def test_cpp_rejects_applicable_invalid_contract_vectors(native_solver, vector):
    calculation = vector["request"]["calculation"]
    result = subprocess.run(
        [
            str(native_solver),
            calculation["initial_velocity_m_s"],
            calculation["acceleration_m_s2"],
            calculation["time_s"],
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("initial_velocity", "acceleration", "time", "message"),
    [
        ("1.5", "2", "4", "exact integer or fraction strings"),
        ("100001", "2", "4", "exceeds native capability bounds"),
        ("3", "2/0", "4", "exceeds native capability bounds"),
    ],
)
def test_cpp_constant_acceleration_rejects_unsupported_inputs(
    native_solver,
    initial_velocity,
    acceleration,
    time,
    message,
):
    result = subprocess.run(
        [str(native_solver), initial_velocity, acceleration, time],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert message in result.stderr


def test_cpp_constant_acceleration_rejects_wrong_argument_count(native_solver):
    result = subprocess.run(
        [str(native_solver), "3", "2"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("usage:")
