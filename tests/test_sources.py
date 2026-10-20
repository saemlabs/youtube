import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from saemphysics.cli import main
from saemphysics.models import RightsStatus
from saemphysics.sources import (
    SourceDocument,
    SourceManifest,
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

    assert len(manifest.documents) == 29
    assert all(
        document.rights_status == RightsStatus.REVIEW_REQUIRED
        for document in manifest.documents
    )
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
        "document_count": 29,
        "rights_review_required": 29,
        "ingestion_status_counts": {
            "catalogued": 29,
            "extraction_pending": 0,
            "extracted": 0,
            "human_reviewed": 0,
        },
    }
