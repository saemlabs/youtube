# SaemPhysics project principles and source policy

This document records the owner's intended direction. It guides future
architecture and content work; it does not mean that cloud infrastructure,
source permissions, or religious-source review have already been completed.

## One learning engine

- Build one student-to-teacher model with a stable, versioned request/response
  contract. Student pages, teacher tools, APIs, and future native components
  must route through that shared engine rather than duplicate its learning,
  solving, or trust rules.
- Grow through small, working vertical slices: a learner asks or practices,
  the system responds with supported work, and the response carries evidence,
  provenance, and limitations.
- Python is the active application and orchestration layer. C, C++, and
  C#/.NET are future implementation options for specific capabilities, not
  parallel models. Any such component must meet the shared contract and
  conformance tests.
- The long-term research direction may include a cognitive operating system
  and quantum-computing experiments. These are aspirations, not current
  product capabilities or deployment claims.

## Cloud direction: Google Cloud and AWS

The intended hosting direction is to use Google Cloud and/or AWS facilities
for future frontend and backend deployments. No cloud service, account, region,
or production environment is configured by this statement.

- Keep application logic and the contract portable; avoid provider-specific
  assumptions in the learning engine.
- Choose a primary provider and any secondary-provider role only after
  comparing the actual requirements for hosting, storage, identity, networking,
  observability, backup, cost, and operational ownership.
- Before processing real learner data, define data minimization, retention and
  deletion, encryption, access controls, secrets management, backups, incident
  response, applicable legal requirements, and user-facing privacy notices.
- Select deployment regions and subprocessors deliberately. Do not send
  student submissions or source files to third-party AI services unless the
  owner has approved the service, data handling, and rights for that use.
- Keep the present local workbench loopback-only until these controls are
  designed and tested. A cloud vendor's facilities are not by themselves a
  complete security or privacy design.

## Educational knowledge sources: MIT OpenCourseWare

MIT OpenCourseWare and relevant MIT faculty materials are intended as important
educational references for mathematics, computing, physics, and related
subjects. A course, professor, or institution is not blanket permission to
copy or redistribute its material, nor does source use imply endorsement.

- Review the specific course/resource license and terms before downloading,
  storing, adapting, displaying, or redistributing any material. Permissions
  can differ by resource.
- Preserve a source record for each used resource: title, author/instructor,
  course, stable URL, version/date when available, applicable license, access
  date, and the exact sections/pages used.
- Record these fields in the source catalog where known. A source may remain
  catalogued with unknown metadata, but an item marked `licensed` must include
  the license name, official license URL, and a human-readable rights-evidence
  note.
- Prefer original explanations and problem material. Attribute sources for
  ideas and facts; do not reproduce protected course text, figures, or
  recordings beyond the rights granted.
- Treat extracted notes or machine-generated summaries as candidates. A
  human reviewer checks accuracy, attribution, and rights before they become
  trusted teaching content.
- Keep the repository source manifest's rights status explicit. Existing
  catalog entries marked `review_required` remain uncleared until their
  individual rights evidence is reviewed.

## Ethical foundation and religious-source handling

The owner's intended ethical inspiration is the life and sayings of Prophet
Muhammad, using authentic narrations and scholarship associated with
recognized scholars and institutions in the Deoband and Medina traditions.
This is a project value statement, not a religious ruling or claim that any
particular narration or interpretation has already been authenticated.

- Do not invent, paraphrase as a quotation, or attribute a saying to the
  Prophet without a traceable source. Record the collection, book/chapter or
  hadith identifier, edition or stable link, narrator where available, and
  the grading/authentication source rather than relying on an unsourced
  internet quotation.
- Attribute scholarly explanations to the named scholar and work, including
  edition or link and relevant context. Do not imply that all Deobandi or
  Medinan scholars share one view.
- Distinguish primary narration, scholarly interpretation, translation, and
  the system's own educational wording. Preserve meaningful disagreements
  instead of presenting one interpretation as universally settled.
- Require review by a suitably qualified human reviewer before religious
  material is presented as an authenticated teaching, and obtain permission
  before reproducing protected translations or commentary.
- The software may organize sources and present reviewed educational material;
  it must not claim scholarly authority, issue fatwas, or replace qualified
  religious guidance. Generated material remains clearly labeled as a draft.
- Apply the same honesty, care, fairness, respect, and accountability to
  ordinary educational content, learner data, and publishing decisions.

## Operational consequence

Every future content item and service should carry the evidence needed for a
person to answer: where did this come from, who reviewed it, what may we do
with it, what is computed versus interpreted, and what remains uncertain?
Until those answers are available, keep the item in a review-required or draft
state and do not publish it as authoritative.
