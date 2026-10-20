import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from saemphysics.central import StudentRequest, process_student_request


CONTRACT_PATH = (
    Path(__file__).resolve().parents[1] / "contracts/v1/conformance.json"
)


def _contract_vectors():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _response_projection(response):
    payload = response.model_dump(mode="json")
    return {
        "status": payload["status"],
        "artifact": payload["artifact"],
        "verification_status": payload["verification"]["status"],
        "trace_layers": [event["layer"] for event in payload["trace"]],
    }


def test_valid_contract_vectors_match_canonical_processor():
    contract = _contract_vectors()
    assert contract["contract"] == "saemphysics.student-request-response"
    assert contract["schema_version"] == "1.0.0"

    vector_ids = [vector["id"] for vector in contract["valid_vectors"]]
    assert len(vector_ids) == len(set(vector_ids))

    for vector in contract["valid_vectors"]:
        request = StudentRequest.model_validate(vector["request"])
        response = process_student_request(request)
        assert _response_projection(response) == vector["expected"], vector["id"]


@pytest.mark.parametrize(
    "vector",
    _contract_vectors()["invalid_vectors"],
    ids=lambda vector: vector["id"],
)
def test_invalid_contract_vectors_are_rejected_before_execution(vector):
    with pytest.raises(ValidationError):
        StudentRequest.model_validate(vector["request"])
