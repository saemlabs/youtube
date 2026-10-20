import json

import pytest
from pydantic import ValidationError

from saemphysics.concepts import (
    ConceptGraph,
    load_concept_graph,
    validate_question_concepts,
)
from saemphysics.models import QuestionRecord, RightsStatus, SourceRecord


def concept(concept_id, prerequisites=None):
    return {
        "concept_id": concept_id,
        "title": concept_id.replace("_", " ").title(),
        "description": f"Draft definition for {concept_id}.",
        "subject": "physics",
        "prerequisites": prerequisites or [],
    }


def test_project_concept_graph_is_versioned_acyclic_and_unreviewed():
    graph = load_concept_graph("data/concepts.json")

    assert graph.schema_version == "1.0"
    assert {item.concept_id for item in graph.concepts} == {
        "constant_acceleration",
        "displacement",
        "final_velocity",
    }
    assert all(not item.review.human_verified for item in graph.concepts)
    assert next(
        item for item in graph.concepts if item.concept_id == "displacement"
    ).prerequisites == ["constant_acceleration"]


def test_concept_graph_rejects_duplicate_ids():
    with pytest.raises(ValidationError, match="Concept IDs must be unique"):
        ConceptGraph(concepts=[concept("motion"), concept("motion")])


def test_concept_graph_rejects_unknown_prerequisite():
    with pytest.raises(ValidationError, match="unknown prerequisites"):
        ConceptGraph(concepts=[concept("motion", ["unknown"])])


def test_concept_graph_rejects_prerequisite_cycles():
    with pytest.raises(ValidationError, match="contains a cycle"):
        ConceptGraph(
            concepts=[
                concept("motion", ["velocity"]),
                concept("velocity", ["motion"]),
            ]
        )


def test_concept_graph_rejects_duplicate_prerequisites():
    with pytest.raises(ValidationError, match="prerequisite IDs must be unique"):
        ConceptGraph(concepts=[concept("motion"), concept("velocity", ["motion", "motion"])])


def test_question_concept_references_must_exist():
    graph = ConceptGraph(concepts=[concept("motion")])
    question = QuestionRecord(
        question_id="synthetic-motion",
        exam="Synthetic",
        year=2026,
        subject="physics",
        topic="mechanics",
        concepts=["motion", "unknown"],
        source=SourceRecord(
            document_id="synthetic-source",
            rights_status=RightsStatus.ORIGINAL,
        ),
        question_text="A synthetic mechanics question with concept tags.",
    )

    with pytest.raises(ValueError, match="references unknown concepts"):
        validate_question_concepts(question, graph)


def test_concept_graph_loader_rejects_non_object_json(tmp_path):
    path = tmp_path / "concepts.json"
    path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain an object"):
        load_concept_graph(path)
