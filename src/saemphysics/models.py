from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RightsStatus(str, Enum):
    ORIGINAL = "original"
    PUBLIC_DOMAIN = "public_domain"
    LICENSED = "licensed"
    PERMISSION_REQUIRED = "permission_required"
    REVIEW_REQUIRED = "review_required"


class SolutionStatus(str, Enum):
    NOT_SOLVED = "not_solved"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"


class SourceRecord(StrictModel):
    document_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    question_number: str | None = None
    url: HttpUrl | None = None
    rights_status: RightsStatus = RightsStatus.REVIEW_REQUIRED


class AnswerOption(StrictModel):
    key: str = Field(pattern=r"^[A-D]$")
    text: str = Field(min_length=1)


class VerificationCheck(StrictModel):
    name: str = Field(min_length=1)
    passed: bool
    details: str = Field(min_length=1)


class SolutionArtifact(StrictModel):
    status: SolutionStatus = SolutionStatus.NOT_SOLVED
    assumptions: list[str] = Field(default_factory=list)
    derivation_steps: list[str] = Field(default_factory=list)
    symbolic_result: str | None = None
    numerical_result: str | None = None
    units: str | None = None
    verification_checks: list[VerificationCheck] = Field(default_factory=list)

    @model_validator(mode="after")
    def verified_solution_has_evidence(self):
        if self.status == SolutionStatus.VERIFIED:
            if not self.derivation_steps:
                raise ValueError("A verified solution must include derivation steps")
            if not self.verification_checks:
                raise ValueError("A verified solution must include verification checks")
            if not all(check.passed for check in self.verification_checks):
                raise ValueError("A verified solution cannot contain failed checks")
        return self


class ReviewRecord(StrictModel):
    human_verified: bool = False
    reviewer: str | None = None

    @model_validator(mode="after")
    def verified_review_has_reviewer(self):
        if self.human_verified and not self.reviewer:
            raise ValueError("A human-verified record must identify its reviewer")
        return self


class TeachingPlan(StrictModel):
    intuition: str | None = None
    visual_analogy: str | None = None
    common_misconception: str | None = None
    exam_strategy: str | None = None


class QuestionRecord(StrictModel):
    question_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    exam: str = Field(min_length=1)
    year: int = Field(ge=1800, le=2200)
    subject: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    subtopic: str | None = None
    language: str = "en"
    source: SourceRecord
    question_text: str = Field(min_length=1)
    diagram_assets: list[str] = Field(default_factory=list)
    options: list[AnswerOption] = Field(default_factory=list)
    official_answer: str | None = None
    concepts: list[str] = Field(default_factory=list)
    solution: SolutionArtifact = Field(default_factory=SolutionArtifact)
    teaching_plan: TeachingPlan = Field(default_factory=TeachingPlan)
    review: ReviewRecord = Field(default_factory=ReviewRecord)
