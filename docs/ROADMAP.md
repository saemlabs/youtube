# SaemPhysics phased build roadmap

This is a practical sequence toward the SaemPhysics vision, not a promise that
an autonomous AI can safely ingest every exam and publish finished videos.
Each phase should leave a tested, reviewable artifact. Keep the current focus
small, record a short checkpoint at the end of each work session, and carry
unfinished work forward rather than starting parallel systems.

## Working rules

- Work on one vertical slice at a time; prefer one topic and a small verified
  corpus over broad, unreviewed ingestion.
- Preserve source, page/question identifiers, and rights status. Do not
  redistribute material unless its licence permits it.
- Keep source answer keys, computed results, and human-reviewed conclusions
  distinct.
- Treat model-generated OCR, derivations, and storyboards as proposals.
  Deterministic checks and named human reviewers control trust and publication.
- Every phase ends with runnable tests or a demonstrable artifact. If a
  prerequisite is unavailable, finish the safe portion and document the block.
- Use the existing token/context budget for one task at a time. At session end,
  record changed files, validation, the next concrete action, and unresolved
  decisions in a concise checkpoint. Do not spend context re-reading the entire
  library when a relevant source section and code surface will suffice.

## Month 1 — Foundation and canonical question records (starting now)

**Goal:** Make the current verified math path easy to run and establish a
strict, provenance-aware format for a question before collecting a real corpus.

1. Organize and index the supplied documents. **Done:** sources are grouped in
   `docs/` and catalogued in [`README.md`](./README.md).
2. Expose the existing verified math runtime through a JSON command. **Done:**
   `saemphysics run` and its tests.
3. Define one student-facing request/response contract over supported
   capabilities. **Started:** see [`INTERFACE.md`](./INTERFACE.md) and
   `saemphysics interact`.
4. Validate canonical question JSON and add clearly synthetic starter records.
   Five original constant-acceleration examples now pass the corpus and solver
   checks; they remain unsolved/unreviewed in the question bank.
5. Keep source rights and human review explicit. **Exit check:** a malformed
   record is rejected, and the starter example is unmistakably synthetic and
   remains unsolved/unreviewed.

## Month 2 — Small, rights-cleared mechanics pilot

**Goal:** Build a small, manually checked dataset for one narrow mechanics
subtopic (target: 10–20 records, not a mass PDF import).

- Select one exam/source and verify that each question may be stored and used;
  ask the project owner to choose if the repository does not document this.
- Add a source-document manifest with identifier, local path or URL, page
  mapping, licence/rights evidence, and ingestion status.
- Add records one at a time with page/question provenance and validation.
- Keep scans/OCR output separate from human-corrected question text.
- **Exit check:** every pilot record validates, links to its source location,
  records its rights status, and is marked for review when transcription is
  uncertain.

The uploaded reference documents have a catalog at
[`data/sources.json`](../data/sources.json), validated by
`saemphysics validate-sources`. It catalogs the supplied references plus the
synthetic source; selecting and licensing an exam paper remains a separate
Month 2 decision.

The project also has five original synthetic constant-acceleration prompts
for exercising the question schema and solver. They are not exam-corpus
records and do not replace the rights-cleared, manually reviewed pilot.
Their source links and rights labels are checked with
`saemphysics validate-corpus data/questions`.

## Month 3 — Reproducible document and question ingestion

**Goal:** Reduce manual copying errors without treating OCR as truth.

- Implement an importer for a single supported document format.
- Preserve the original; emit candidate text, page references, and extraction
  warnings as separate artifacts.
- Add a review workflow for equations, diagrams, answer choices, and OCR
  confidence; never silently overwrite a reviewed record.
- **Exit check:** a small known document produces repeatable candidate records
  and a reviewer can trace every field to its page.

## Month 4 — Mechanics solver coverage

**Goal:** Expand from constant acceleration only when a narrowly defined model
has explicit assumptions and checks.

- Choose the next mechanic from the pilot (for example, one-dimensional
  work-energy), define typed inputs and units, and implement one solver.
- Add worked examples, boundary/limiting cases, and failure cases before
  wiring it into Semantic IR and the CLI.
- **Exit check:** exact or appropriately bounded numerical results pass
  equation, unit, and assumption checks on a test corpus.

## Month 5 — Mathematical verification and units

**Goal:** Make verification claims more informative than a single CAS result.

- Add dimension/unit representation and checks for the selected mechanics
  slice; reject incompatible inputs explicitly.
- Separate the solver from checks and document when checks share SymPy or
  another implementation (shared engines are not independent verification).
- **Exit check:** incompatible units fail with clear errors and expected unit
  transformations have regression coverage.

## Month 6 — Concept graph and learning metadata

**Goal:** Connect questions to a small, reviewable set of concepts and
prerequisites.

- Define versioned concept records and prerequisite edges for the pilot topic.
- Add concept identifiers to question records and validate references.
- Record teaching moves (physical intuition, assumptions, limiting case,
  misconception) without imitating any author's protected expression.
- **Exit check:** a graph validation test catches unknown concepts and cycles;
  the pilot questions map to reviewed concepts.

## Month 7 — Structured explanation plans

**Goal:** Turn verified derivations into a constrained lesson outline.

- Define a versioned lesson/storyboard schema tied to question and verification
  IDs.
- Require claims and displayed equations to reference approved solution
  artifacts; mark model-authored wording as a draft.
- Add validation and review states; no provider API is required yet.
- **Exit check:** valid drafts compile, unverified claims are rejected, and
  questions with unresolved source/review status cannot be published.

## Month 8 — First reviewed visual lesson

**Goal:** Render one short original lesson from the structured plan.

- Add a reusable renderer for the selected mechanics concept and a scene-level
  visual model test.
- Render in a supported environment; review equation timing, units, motion,
  narration/captions, and attribution.
- **Exit check:** a human science/teaching review is recorded and all required
  rights clearances are present before any public release.

## Month 9 — Connect the learner-facing prototype

**Goal:** Connect one existing browser prototype to the trusted backend.

- Choose either Exam Forecaster or Mock Tester and specify the smallest user
  flow.
- Add a typed API boundary only after input/output schemas and error behavior
  are defined; do not expose arbitrary code execution.
- **Exit check:** one validated question can be loaded, answered, and shown
  with a verified result and provenance.

## Month 10 — Exam-topic analytics

**Goal:** Provide evidence-based topic summaries over the rights-cleared pilot.

- Count only reviewed records; preserve exam/year/source metadata and show
  corpus coverage and missing years.
- Add tests for duplicate questions, missing labels, and misleading small
  samples.
- **Exit check:** analytics report its dataset and limitations and never
  presents the pilot as a complete exam forecast.

## Month 11 — Reliability and controlled expansion

**Goal:** Improve the proven path before adding another topic or exam.

- Add import/solver/lesson regression fixtures, reproducible builds, backup
  guidance, and actionable diagnostics.
- Expand the corpus only if rights, review capacity, and validation quality
  remain manageable.
- **Exit check:** a clean setup reproduces tests and sample artifacts; issues
  are traceable to source, interpretation, solving, or rendering.

## Month 12 — Release readiness and next-year plan

**Goal:** Decide what is safe to release and what remains research.

- Audit provenance, rights, human approvals, dependency security, and all
  public-facing claims.
- Publish only reviewed lessons and supported features; keep uncertain work
  visibly in draft/review states.
- Review the year's measured outcomes and define the next 12-month scope.
- **Exit check:** a release checklist passes or the product remains explicitly
  private/experimental with blockers recorded.

## Start today — Phase 1, task 1

Use the synthetic record at
[`data/questions/synthetic_constant_acceleration.json`](../data/questions/synthetic_constant_acceleration.json).
Validate it with:

```bash
saemphysics validate-question data/questions/synthetic_constant_acceleration.json
```

Then run its matching calculation:

```bash
saemphysics run examples/requests/constant_acceleration.json
```

Today’s implementation adds the question validator and synthetic record. The
next Phase 1 action is to run both commands and tests, then document the
question-source manifest before selecting any real exam material.
