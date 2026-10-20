# SaemPhysics unified engine direction

## One model, many interfaces

The project has one canonical student request/response contract:

1. A user interface collects a typed request.
2. The request is validated as `StudentRequest`.
3. `process_student_request` routes it to a registered capability.
4. The capability returns a `StudentResponse` with results, verification,
   trace, and any review limitations.
5. Interfaces render that response; they do not reimplement solving, grading,
   or trust decisions.

The current Python workbench and the Python-rendered student page both use this
same processor and the same source-validated question corpus. The Python page
is a small first student/teacher workflow: it links to the SaemPhysics YouTube
channel, presents a corpus question, accepts an answer, and shows feedback
only after submission. `/` retains the full visual workbench; `/student`
opens the focused student page.

## Language boundaries

Python is the current application and orchestration layer. It owns request
validation, corpus/provenance checks, routing, user-facing errors, and the
current verified math path. C, C++, and C#/.NET are planned implementation
languages for future engine capabilities, not active backends yet.

Before a native component is introduced, define a versioned, language-neutral
capability request and response from the existing student/engine contract.
Then integrate the component behind the capability boundary and require it to
pass the same conformance vectors as the Python implementation. The C/C++
boundary and C#/.NET transport should be selected for a specific capability
and measurable need; they must not create separate question schemas,
verification policies, or user-facing APIs.

The first executable compatibility baseline is
[`contracts/v1/conformance.json`](../contracts/v1/conformance.json), documented
in [`contracts/v1/README.md`](../contracts/v1/README.md). It covers exact
derivative, constant-acceleration, definite-integral, and linear-system results,
ordered trace layers, verification status, and invalid-input rejection. Python
runs these vectors against the canonical processor in
[`tests/test_contract_vectors.py`](../tests/test_contract_vectors.py).

Initial constraints:

- Keep one source of truth for request and response schemas.
- Pass typed, bounded values to engine capabilities; never execute submitted
  source code or arbitrary commands.
- Preserve exactness, units, assumptions, verification evidence, and
  provenance across any language boundary.
- Label shared-library or CAS checks accurately; two wrappers around the same
  implementation are not independent verification.
- Add a capability only with tests for valid inputs, invalid inputs, limits,
  determinism, and cross-language contract compatibility.
- Keep local interfaces loopback-only until authentication, privacy, and
  deployment controls are designed.

## Growth toward the larger vision

The student/teacher workflow is the first vertical slice, not a separate
product. The same request path can grow from practice into reviewed
explanations, lesson plans, visual rendering, learner progress, and eventually
research experiments for quantum-computing targets. Each step must preserve
the same typed boundaries and review gates. Quantum execution, adaptive AI
teaching, durable learner accounts, and public publishing are future work and
are not implied by this prototype.

The connected outcomes and ordered implementation path are described in
[`THREE_VISION_BUILD.md`](./THREE_VISION_BUILD.md): teacher-created lessons,
the learner platform reusing those reviewed artifacts, and the cognitive/quantum
research direction all build on the same engine rather than separate models.

Cloud direction, educational-source rights, and the owner's intended ethical
source-review principles are recorded in
[`PROJECT_PRINCIPLES.md`](./PROJECT_PRINCIPLES.md). Those principles describe
future requirements; they do not mean that a cloud deployment or source
authentication has been completed.

The source catalog supports structured author/instructor, course, version,
license, and access-date metadata. `review_required` remains the default; a
record marked `licensed` must provide the license name, official URL, and
rights-evidence note. The schema records evidence but cannot itself determine
whether an interpretation of a license is legally correct.

The versioned concept graph at [`data/concepts.json`](../data/concepts.json)
is the first cognitive structure shared by questions and interfaces. Graph
validation rejects duplicate IDs, unknown prerequisites, cycles, and question
references to missing concepts. Its starter definitions are explicitly
unreviewed; graph validity is structural correctness, not pedagogical approval.
