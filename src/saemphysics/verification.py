from dataclasses import dataclass

from saemphysics.models import QuestionRecord, RightsStatus, SolutionStatus


@dataclass(frozen=True)
class PublicationDecision:
    publishable: bool
    blockers: tuple[str, ...]


def publication_decision(question: QuestionRecord) -> PublicationDecision:
    """Require solver evidence, human review, and cleared reuse rights."""
    blockers = []

    if question.solution.status != SolutionStatus.VERIFIED:
        blockers.append("The solution has not passed verification.")
    if not question.solution.verification_checks:
        blockers.append("No verification evidence is recorded.")
    elif not all(check.passed for check in question.solution.verification_checks):
        blockers.append("One or more verification checks failed.")
    if not question.review.human_verified:
        blockers.append("A human reviewer has not approved the question.")
    if question.source.rights_status not in {
        RightsStatus.ORIGINAL,
        RightsStatus.PUBLIC_DOMAIN,
        RightsStatus.LICENSED,
    }:
        blockers.append("Source rights are not cleared for publication.")

    return PublicationDecision(publishable=not blockers, blockers=tuple(blockers))
