import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/CORE_PROCESSOR_BOOK_MATRIX.csv"
SOURCE_MANIFEST = ROOT / "data/sources.json"


def test_core_processor_book_matrix_covers_each_uploaded_reference():
    with MATRIX.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, strict=True))
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    references = {
        document["document_id"]: document
        for document in manifest["documents"]
        if document.get("rights_status") != "original"
    }

    assert len(rows) == len(references)
    assert {row["source_id"] for row in rows} == set(references)
    assert len({row["source_id"] for row in rows}) == len(rows)
    for row in rows:
        source = references[row["source_id"]]
        assert row["category"] == source["category"]
        assert (ROOT / source["path"]).is_file()
        assert row["title"].strip()
        assert row["chapters_or_sections"].strip()
        assert row["topics"].strip()
        assert row["concepts"].strip()
        assert row["math_and_computing_capabilities"].strip()
        assert row["processor_mapping"].strip()
        assert row["evidence"].strip()
        assert row["coverage_status"].strip()
