from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, HttpUrl, model_validator

from saemphysics.models import RightsStatus, StrictModel


class PageMapping(StrictModel):
    page: int = Field(ge=1)
    label: str = Field(min_length=1)


class SourceDocument(StrictModel):
    document_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    category: Literal["computing", "mathematics", "physics", "quantum", "vision"]
    path: str | None = Field(default=None, min_length=1)
    url: HttpUrl | None = None
    rights_status: RightsStatus = RightsStatus.REVIEW_REQUIRED
    rights_evidence: str | None = None
    ingestion_status: Literal[
        "catalogued",
        "extraction_pending",
        "extracted",
        "human_reviewed",
    ] = "catalogued"
    page_mapping: list[PageMapping] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source_metadata(self):
        if self.path is None and self.url is None:
            raise ValueError("A source requires a local path or a URL")
        if self.path is not None:
            relative_path = PurePosixPath(self.path)
            raw_parts = self.path.split("/")
            if (
                "\\" in self.path
                or relative_path.is_absolute()
                or any(part in {"", ".", ".."} for part in raw_parts)
            ):
                raise ValueError(
                    "Source paths must be normalized repository-relative paths"
                )
        if self.rights_status != RightsStatus.REVIEW_REQUIRED and not (
            self.rights_evidence and self.rights_evidence.strip()
        ):
            raise ValueError(
                "A rights evidence note is required when rights are not awaiting review"
            )
        pages = [entry.page for entry in self.page_mapping]
        if len(pages) != len(set(pages)):
            raise ValueError("Page mappings must use unique page numbers")
        return self


class SourceManifest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    documents: list[SourceDocument] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_documents(self):
        ids = [document.document_id for document in self.documents]
        paths = [
            document.path for document in self.documents if document.path is not None
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("Document IDs must be unique in the source manifest")
        if len(paths) != len(set(paths)):
            raise ValueError("Document paths must be unique in the source manifest")
        return self


def validate_source_files(
    manifest: SourceManifest,
    project_root: str | Path,
) -> None:
    """Ensure each catalogued local file exists inside the selected project root."""
    root = Path(project_root).resolve()
    for document in manifest.documents:
        if document.path is None:
            continue
        target = root.joinpath(*PurePosixPath(document.path).parts).resolve()
        if not target.is_relative_to(root):
            raise ValueError(
                f"Source {document.document_id!r} resolves outside the project root"
            )
        if not target.is_file():
            raise ValueError(
                f"Source file for {document.document_id!r} does not exist: "
                f"{document.path}"
            )
