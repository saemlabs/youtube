import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from saemphysics.models import QuestionRecord, ReviewRecord, StrictModel


class ConceptRecord(StrictModel):
    concept_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    review: ReviewRecord = Field(default_factory=ReviewRecord)

    @model_validator(mode="after")
    def validate_prerequisites(self):
        if len(self.prerequisites) != len(set(self.prerequisites)):
            raise ValueError("Concept prerequisite IDs must be unique")
        if self.concept_id in self.prerequisites:
            raise ValueError("A concept cannot be its own prerequisite")
        return self


class ConceptGraph(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    concepts: list[ConceptRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self):
        records = {concept.concept_id: concept for concept in self.concepts}
        if len(records) != len(self.concepts):
            raise ValueError("Concept IDs must be unique")

        for concept in self.concepts:
            unknown = set(concept.prerequisites) - records.keys()
            if unknown:
                raise ValueError(
                    f"Concept {concept.concept_id!r} has unknown prerequisites: "
                    + ", ".join(sorted(unknown))
                )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(concept_id: str) -> None:
            if concept_id in visiting:
                raise ValueError(
                    f"Concept prerequisite graph contains a cycle at {concept_id!r}"
                )
            if concept_id in visited:
                return
            visiting.add(concept_id)
            for prerequisite in records[concept_id].prerequisites:
                visit(prerequisite)
            visiting.remove(concept_id)
            visited.add(concept_id)

        for concept_id in records:
            visit(concept_id)
        return self


def load_concept_graph(path: str | Path) -> ConceptGraph:
    """Read and validate a versioned concept graph from JSON."""
    content = Path(path).read_text(encoding="utf-8")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Concept graph JSON must contain an object")
    return ConceptGraph.model_validate(payload)


def validate_question_concepts(
    question: QuestionRecord,
    graph: ConceptGraph,
) -> None:
    """Ensure every concept referenced by a question exists in the graph."""
    known_ids = {concept.concept_id for concept in graph.concepts}
    unknown = set(question.concepts) - known_ids
    if unknown:
        raise ValueError(
            f"Question {question.question_id!r} references unknown concepts: "
            + ", ".join(sorted(unknown))
        )
