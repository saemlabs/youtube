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
canonical verified math path. C, C++, and C#/.NET currently implement one
opt-in native capability; they are not yet complete replacements for Python
orchestration or the full engine.

For each additional native component, define a versioned, language-neutral
capability request and response from the existing student/engine contract.
Integrate it behind the capability boundary and require it to pass the same
conformance vectors as the Python implementation. The C/C++
boundary and C#/.NET transport are selected for a specific capability and
measurable need; they must not create separate question schemas,
verification policies, or user-facing APIs.

The first executable compatibility baseline is
[`contracts/v1/conformance.json`](../contracts/v1/conformance.json), documented
in [`contracts/v1/README.md`](../contracts/v1/README.md). It covers exact
derivative, constant-acceleration, definite-integral, and linear-system results,
ordered trace layers, verification status, and invalid-input rejection. Python
runs these vectors against the canonical processor in
[`tests/test_contract_vectors.py`](../tests/test_contract_vectors.py).

The first native capability is exact constant-acceleration kinematics:
[`native/cpp/constant_acceleration.cpp`](../native/cpp/constant_acceleration.cpp),
[`native/c/constant_acceleration.c`](../native/c/constant_acceleration.c), and
[`native/csharp/Program.cs`](../native/csharp/Program.cs). Each implements
bounded exact rational arithmetic and emits the same result sub-artifact.
The C and C++ implementations use compiler-supported 128-bit integers; C#
uses `BigInteger` while applying the same input bounds. Tests compile all
available implementations and compare them with shared vectors covering
integer, fractional, negative-acceleration, and zero-acceleration cases.
An explicit Python adapter can invoke any resulting executable through
`saemphysics interact --native-kinematics PATH` or
`saemphysics web --native-kinematics PATH`. The adapter compares the native
result exactly with the canonical Python solver, retains Python verification,
and records the native execution in the trace. A mismatch, invalid response,
timeout, or process failure is an explicit error; there is no silent fallback.
The native programs still do not implement the complete `StudentResponse`,
verification, or trace contract themselves, and Python remains authoritative.

The capability-level response envelope is versioned at
[`contracts/v1/native-capability-response.schema.json`](../contracts/v1/native-capability-response.schema.json).
At the application boundary, Python remains the coordinator: it validates the
complete student request, compiles a capability plan, invokes the native
operation only when configured, validates the envelope, independently
cross-checks the exact result and verification, and emits the canonical
student-facing response and trace. This composes small native mechanisms
without duplicating corpus, lesson, grading, or human-review policies in three
languages.

This is a deliberately narrow engineering step informed by the uploaded
programming, computation, calculus, and mechanics references: keep one logical
capability contract independent of its implementation language, make exact
state and limits visible, and validate the concrete mechanism before
generalizing it. Feynman's mechanics discussion builds distance from velocity
and velocity from acceleration through integration; this implementation uses
the corresponding constant-acceleration model `v(t) = u + at` and displacement
as the integral of velocity. Euler's complex-exponential identity is not
needed for this scalar mechanics capability; it belongs in later typed
wave/phase work rather than being forced into this model. Neither this
capability nor the language split is a quantum algorithm or evidence of a
quantum advantage. The uploaded C* material's distinction between logical data
positions and physical layout is a useful future design constraint, not a
reason to label this scalar solver as parallel or hardware-independent.

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
