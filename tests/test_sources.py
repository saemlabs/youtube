import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from saemphysics.cli import main
from saemphysics.ir import SemanticIR, compile_request
from saemphysics.models import RightsStatus
from saemphysics.runtime import execute_plan
from saemphysics.sources import (
    SourceDocument,
    SourceManifest,
    load_question_corpus,
    validate_source_files,
)


def make_document(**updates):
    fields = {
        "document_id": "reference-book",
        "title": "Reference book",
        "category": "computing",
        "path": "docs/reference.pdf",
        "rights_status": RightsStatus.REVIEW_REQUIRED,
        "ingestion_status": "catalogued",
    }
    fields.update(updates)
    return SourceDocument(**fields)


def test_manifest_catalogs_every_uploaded_pdf_and_docx():
    manifest = SourceManifest.model_validate_json(
        Path("data/sources.json").read_text(encoding="utf-8")
    )

    assert len(manifest.documents) == 30
    assert all(
        document.rights_status == RightsStatus.REVIEW_REQUIRED
        for document in manifest.documents
        if document.document_id != "saemphysics-original-mechanics-pilot"
    )
    assert sum(
        document.rights_status == RightsStatus.REVIEW_REQUIRED
        for document in manifest.documents
    ) == 29
    assert all(document.ingestion_status == "catalogued" for document in manifest.documents)


def test_manifest_rejects_duplicate_ids_and_paths():
    first = make_document()
    duplicate_id = make_document(path="docs/another.pdf")
    duplicate_path = make_document(document_id="another-id")

    with pytest.raises(ValidationError, match="Document IDs must be unique"):
        SourceManifest(documents=[first, duplicate_id])
    with pytest.raises(ValidationError, match="Document paths must be unique"):
        SourceManifest(documents=[first, duplicate_path])


@pytest.mark.parametrize(
    "path",
    [
        "../outside.pdf",
        "/etc/passwd",
        "docs/../secret.pdf",
        "docs//reference.pdf",
        "docs\\reference.pdf",
    ],
)
def test_source_paths_must_be_repository_relative(path):
    with pytest.raises(ValidationError, match="repository-relative"):
        make_document(path=path)


def test_non_review_rights_status_requires_evidence():
    with pytest.raises(ValidationError, match="rights evidence note"):
        make_document(rights_status=RightsStatus.LICENSED)


def test_licensed_source_requires_license_name_and_official_url():
    with pytest.raises(ValidationError, match="license name and its official URL"):
        make_document(
            rights_status=RightsStatus.LICENSED,
            rights_evidence="The source permits reuse under a license.",
        )


def test_source_attribution_and_license_metadata_are_structured():
    document = make_document(
        author_or_instructor="Example Instructor",
        course="Example Course 1.001",
        version="Fall 2026",
        url="https://example.org/course",
        rights_status=RightsStatus.LICENSED,
        rights_evidence="The linked course page identifies the applicable license.",
        license_name="Creative Commons Attribution 4.0 International",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        accessed_on="2026-10-20",
    )

    assert document.author_or_instructor == "Example Instructor"
    assert document.course == "Example Course 1.001"
    assert document.version == "Fall 2026"
    assert str(document.license_url) == "https://creativecommons.org/licenses/by/4.0/"
    assert document.accessed_on.isoformat() == "2026-10-20"


def test_license_name_and_url_must_be_recorded_together():
    with pytest.raises(ValidationError, match="must be recorded together"):
        make_document(
            license_name="Creative Commons Attribution",
            rights_status=RightsStatus.REVIEW_REQUIRED,
        )


def test_remote_source_can_be_catalogued_without_a_local_path():
    document = make_document(path=None, url="https://example.org/source.pdf")

    assert document.path is None
    assert str(document.url) == "https://example.org/source.pdf"


def test_page_mapping_must_have_unique_pages():
    with pytest.raises(ValidationError, match="unique page numbers"):
        make_document(
            page_mapping=[
                {"page": 3, "label": "chapter"},
                {"page": 3, "label": "appendix"},
            ]
        )


def test_source_file_validation_requires_existing_files_and_rejects_escape(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/reference.pdf").write_text("reference", encoding="utf-8")
    validate_source_files(SourceManifest(documents=[make_document()]), tmp_path)

    missing = make_document(path="docs/missing.pdf")
    with pytest.raises(ValueError, match="does not exist"):
        validate_source_files(SourceManifest(documents=[missing]), tmp_path)


def test_cli_validates_the_uploaded_source_catalog(capsys):
    assert main(["validate-sources", "data/sources.json"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "valid": True,
        "document_count": 30,
        "rights_review_required": 29,
        "ingestion_status_counts": {
            "catalogued": 30,
            "extraction_pending": 0,
            "extracted": 0,
            "human_reviewed": 0,
        },
    }


def test_pilot_corpus_records_match_catalogued_original_source():
    manifest = SourceManifest.model_validate_json(
        Path("data/sources.json").read_text(encoding="utf-8")
    )
    questions = load_question_corpus("data/questions", manifest)

    assert len(questions) == 5
    assert len({question.question_id for question in questions}) == 5
    assert all(
        question.source.document_id == "saemphysics-original-mechanics-pilot"
        and question.source.rights_status == RightsStatus.ORIGINAL
        and question.solution.status.value == "not_solved"
        and not question.review.human_verified
        for question in questions
    )


def test_each_synthetic_pilot_prompt_has_a_passing_exact_solver_case():
    manifest = SourceManifest.model_validate_json(
        Path("data/sources.json").read_text(encoding="utf-8")
    )
    questions = load_question_corpus("data/questions", manifest)
    cases = {
        "synthetic-constant-acceleration-001": ("3", "2", "4", "28", "11", "28 m; 11 m/s"),
        "synthetic-constant-acceleration-002": ("4", "3/2", "2", "11", "7", "11 m; 7 m/s"),
        "synthetic-constant-acceleration-003": ("5", "-1", "3", "21/2", "2", "10.5 m; 2 m/s"),
        "synthetic-constant-acceleration-004": ("-2", "2", "2", "0", "2", "0 m; 2 m/s"),
        "synthetic-constant-acceleration-005": ("3", "0", "5", "15", "3", "15 m; 3 m/s"),
    }

    for question in questions:
        (
            initial_velocity,
            acceleration,
            time,
            displacement,
            final_velocity,
            answer_text,
        ) = cases[question.question_id]
        result = execute_plan(
            compile_request(
                SemanticIR(
                    operation="solve_constant_acceleration",
                    question_id=question.question_id,
                    initial_velocity_m_s=initial_velocity,
                    acceleration_m_s2=acceleration,
                    time_s=time,
                )
            )
        )
        assert result.result.displacement_m == displacement
        assert result.result.final_velocity_m_s == final_velocity
        assert result.verification.status == "passed"
        assert question.official_answer is not None
        correct_option = next(
            option
            for option in question.options
            if option.key == question.official_answer
        )
        assert correct_option.text == answer_text


def test_corpus_rejects_unknown_source_and_mismatched_rights(tmp_path):
    question_dir = tmp_path / "questions"
    question_dir.mkdir()
    manifest = SourceManifest(
        documents=[
            make_document(
                path="docs/reference.pdf",
            )
        ]
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/reference.pdf").write_text("source", encoding="utf-8")
    question = {
        "question_id": "pilot-question",
        "exam": "Synthetic pilot",
        "year": 2026,
        "subject": "physics",
        "topic": "mechanics",
        "source": {
            "document_id": "unknown-document",
            "rights_status": "review_required",
        },
        "question_text": "A synthetic test question.",
    }
    (question_dir / "question.json").write_text(json.dumps(question), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown source"):
        load_question_corpus(question_dir, manifest, tmp_path)

    question["source"]["document_id"] = "reference-book"
    question["source"]["rights_status"] = "original"
    (question_dir / "question.json").write_text(json.dumps(question), encoding="utf-8")
    with pytest.raises(ValueError, match="rights status does not match"):
        load_question_corpus(question_dir, manifest, tmp_path)


def test_cli_validates_the_complete_synthetic_pilot(capsys):
    assert main(["validate-corpus", "data/questions"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "valid": True,
        "question_count": 5,
        "question_ids": [
            "synthetic-constant-acceleration-001",
            "synthetic-constant-acceleration-002",
            "synthetic-constant-acceleration-003",
            "synthetic-constant-acceleration-004",
            "synthetic-constant-acceleration-005",
        ],
        "source_document_ids": ["saemphysics-original-mechanics-pilot"],
        "all_unsolved": True,
    }
