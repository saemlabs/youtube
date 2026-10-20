# Student-to-teacher interface

The current central processing entry point is `process_student_request` in
`src/saemphysics/central.py`. It accepts one validated `StudentRequest` and
returns a structured `StudentResponse`. The CLI exposes the same contract:

```bash
saemphysics interact examples/requests/student_solve.json
saemphysics interact -
```

The interactive browser workbench uses the same central router through a
local-only HTTP adapter:

```bash
saemphysics web
```

Open `/student` on the same local server for a small Python-rendered
student/teacher page. It links to the SaemPhysics YouTube profile and uses
`process_student_request` for both question practice and answer grading; it
does not contain a separate solver or grading implementation.

It serves the UI and JSON endpoints from one origin, reads questions from the
source-validated corpus, and renders result/check/trace data. The visualization
is a browser-side plot of the solver's exact constant-acceleration inputs; the
solver's exact result and verification report remain authoritative. The
workbench is a development tool bound to loopback, with no authentication,
durable accounts, or public deployment configuration.

The interface is deliberately a small router over registered capabilities.
It is not a general AI agent, does not run arbitrary submitted code, and does
not claim that unavailable capabilities have been completed.

## Request shape

Every request has an `intent`. The model rejects fields that do not belong to
that intent.

### Solve

```json
{
  "intent": "solve",
  "calculation": {
    "operation": "differentiate",
    "question_id": "student-question-001",
    "expression": "x**2"
  }
}
```

Supported calculations are the exact operations accepted by Semantic IR:
constant-acceleration motion, differentiation, definite integration, and exact
square linear-system solving. Unsupported or approximate operations fail
explicitly. The response contains the typed result, verification checks, and
execution trace.

### Practice and answer submission

List the available corpus records without revealing answer keys:

```bash
saemphysics list-questions
```

Select a question by ID; the CLI loads it from the source-validated corpus:

```json
{
  "intent": "practice",
  "question_id": "synthetic-constant-acceleration-001"
}
```

Run the sample with:

```bash
saemphysics interact examples/requests/student_practice.json
```

The central processor accepts a question ID only when supplied with a
validated-corpus resolver. The CLI performs that lookup using
`data/sources.json` and `data/questions`, so students do not need to resend the
full record. Unknown IDs and invalid source/rights links fail explicitly.

The existing embedded-record form remains available to trusted callers:

```json
{
  "intent": "practice",
  "question": {
    "...": "a complete canonical QuestionRecord"
  }
}
```

Practice returns the question and available choices without exposing the
answer key. The student then submits an option:

```json
{
  "intent": "submit_answer",
  "question": {
    "...": "the same complete canonical QuestionRecord"
  },
  "selected_option": "B"
}
```

Grading is currently single-question and stateless. It uses the recorded
official answer only when that answer matches one of the stored option keys.
It does not invent an answer or persist scores. After submission, verified
solution steps may be returned; an unverified explanation remains unavailable.

### Multi-question tests

Start a test from selected corpus IDs:

```json
{
  "intent": "start_test",
  "question_ids": [
    "synthetic-constant-acceleration-001",
    "synthetic-constant-acceleration-002"
  ]
}
```

`start_test` returns question text and options only. Submit one option key for
every same question ID:

```json
{
  "intent": "submit_test",
  "question_ids": [
    "synthetic-constant-acceleration-001",
    "synthetic-constant-acceleration-002"
  ],
  "answers": {
    "synthetic-constant-acceleration-001": "B",
    "synthetic-constant-acceleration-002": "A"
  }
}
```

The grader rejects duplicate IDs, missing/extra answers, questions without
options, and any test with an absent or invalid answer key. It reports an
aggregate score and per-question feedback after submission. Attempts are
stateless and not persisted. Synthetic pilot keys are authored for this
project and solver-tested; they are not official exam answer keys.

Worked-solution feedback is included only when a question has a verified
solution (non-empty derivation and all checks passing) and its question review
has a named human reviewer. Otherwise the score is still returned, the
worked-solution field is `null`, and the response names the questions needing
verification/review. A correct answer key by itself is not treated as proof
of a derivation.

### Explain and make a lesson

`explain` assembles stored assumptions, derivation, result, and passing checks
only when the question solution is marked verified. The explanation remains a
draft for teaching review.

`make_lesson` compiles the existing renderer-independent lesson artifact from
that verified record. It does not call an AI provider, render a video, or
publish anything. Lesson and question review plus source rights remain
separate gates.

## Response envelope

Responses contain:

- `intent`: the requested action.
- `status`: `completed`, `ready`, `draft`, `correct`, `incorrect`, or `blocked`.
- `message`: what happened, without claiming unsupported work.
- `artifact`: result, question, explanation, or lesson data when available.
- `verification`: explicit checks when computation or a stored solution supports it.
- `trace`: runtime layers for computation requests.
- `next_action`: a concrete review or follow-up step when needed.

The local HTTP adapter exposes:

- `GET /api/health`: readiness and corpus size.
- `GET /api/questions`: question metadata/options without answer keys.
- `POST /api/interact`: a validated student request and response envelope.

Request bodies are limited to 1 MiB. Unknown paths, malformed input, unsupported
content types, and invalid corpus IDs return explicit errors.

## Growth path

Keep this outer request/response envelope stable as capabilities expand. Add
new intents only when their typed inputs, outputs, safety/rights constraints,
and tests exist. The roadmap stages ingestion, concept mapping, lesson review,
rendering, and learner-facing persistence separately; a future web/API layer
can call this same central function instead of duplicating business rules.

The planned C/C++/C#/.NET engine boundaries and current implementation status
are documented in [`ENGINE_ARCHITECTURE.md`](./ENGINE_ARCHITECTURE.md).

## Design references

- Feynman's computation material motivates making each processing layer and
  trace inspectable rather than hiding work in one opaque step:
  [`Feynmann computation.PDF`](./computing/Feynmann%20computation.PDF).
- SICP motivates keeping the interface, request interpretation, execution,
  and output as composable parts rather than one monolithic routine:
  [`Book 2 SICP.PDF`](./computing/Book%202%20SICP.PDF).
- Strang's computational science and calculus materials inform keeping
  mathematical objects and verified operations explicit:
  [Computational Science and Engineering](./computing/Gilbert%20Strang%20MIT%20Computational%20Science%20and%20Engineering%20%281%29.docx)
  and [MIT 18.001 calculus](./mathematics/mitres_18_001_gilbert%20strang.pdf).

The interface applies those ideas to the code that exists now; these
references do not imply that ingestion, AI teaching, adaptive tests, or video
rendering are already implemented.
