# SaemPhysics: what exists and what comes next

This note is a working handoff for starting the next development session
without rereading the full repository. It separates implemented, tested
capabilities from drafts, future work, and release blockers.

## Current direction

SaemPhysics is being built as one learning engine with three connected
outcomes:

1. A student and teacher learning platform.
2. A workflow for creating reviewed physics teaching materials and lessons.
3. A longer-term research direction for a composable cognitive system and
   carefully scoped quantum-computing experiments.

The first two have narrow working software slices. The third is a research
vision, not a current product capability. See the
[three-vision build path](./THREE_VISION_BUILD.md) for the intended order.
The product ambition is broad physics and mathematics coverage; the current
constant-acceleration work is only an initial example, not the subject scope.
Build breadth as a curriculum and capability map, then implement and verify
topics incrementally rather than claiming completeness prematurely.

## Built and tested

- **One typed processing path:** Python validates student requests, routes
  registered operations, and returns results with checks and an execution
  trace. The browser and CLI reuse this processor.
- **Exact math capabilities:** constant-acceleration motion, differentiation,
  definite integration, and bounded exact square linear systems.
- **Optional native implementations:** C, C++, and C# implementations cover
  bounded constant-acceleration and small linear-system solves. Python checks
  their results against its canonical implementation; Python remains the
  application coordinator.
- **Mechanics practice:** a small synthetic constant-acceleration question
  corpus supports practice and stateless tests. It is not a licensed,
  comprehensive exam bank, and records/content still require appropriate
  human review.
- **Probability primitives:** explicit distributions, entropy, seeded
  sampling, and Bayesian updates exist as opt-in mathematical foundations.
  They do not make existing answer or solve decisions probabilistic.
- **Teacher workflow:** a local studio creates an unsaved, review-required
  lesson draft from a narrow original mechanics example. It does not render,
  approve, or publish a video.
- **Student and resource interfaces:** the local `/student` page provides
  practice and math tools. `/products` is a preview of an original
  constant-acceleration study pack; its content is still awaiting teacher
  review.
- **Tests:** the repository test suite passed with 213 tests at the time of
  this note. Re-run tests after further changes.

## Browser page and hosting boundary

The GitHub Pages site is configured for
<https://saemlabs.github.io/youtube/> as a separate, responsive, static
introduction designed for current desktop and mobile browsers. It links to the
SaemPhysics YouTube channel and repository and accurately states that the
interactive workbench is not hosted there. The GitHub Actions workflow
publishes only the contents of `site/` after site changes are pushed to `main`.

GitHub Pages serves static files only. It does not run the Python processor,
student practice API, teacher studio, or checkout. The interactive app remains
bound to loopback; do not expose it publicly until authentication, privacy,
deployment, monitoring, and operational controls have been designed and
reviewed. The Pages preview does not collect student data, use analytics, or
offer checkout.

## Not ready to claim or launch

- The starter study pack needs teacher/subject review before it is represented
  as approved teaching material or sold.
- Checkout remains disabled by default. Provider eligibility, exact checkout
  prices, seller details, policies, tax/legal responsibilities, and manual
  fulfillment must be verified before any sale.
- The synthetic corpus is a prototype, not an exam prediction service or
  complete curriculum.
- There are no learner accounts, durable progress records, public solver API,
  video publishing, cloud deployment, or production support process.
- The current C/C++/C# capabilities are bounded components, not a complete
  cross-language operating system, arbitrary hardware layer, or quantum
  processor.
- The concept graph and generated lesson wording remain drafts until a
  qualified human review is recorded.

## Recommended next steps

Work in this order; do not start the later phases until their prerequisites
are met.

1. **Map physics and mathematics coverage.** Create a subject-to-capability
   map spanning the intended breadth of physics and mathematics: domains,
   topics, prerequisite relationships, representative problem types, and
   status (implemented, tested, planned, or research). Identify shared
   foundations such as units/dimensions, symbolic and numerical computation,
   assumptions, verification, provenance, and human review. Do not treat this
   map as a claim that every topic is already supported.
2. **Study sources for each planned area.** Use the owner's provided books and
   relevant MIT OpenCourseWare materials to inform the map and implementation.
   Record the exact resource, sections/pages, access or edition details, and
   applicable rights/licence evidence. Check the specific MIT OCW resource's
   terms before copying, adapting, storing, or redistributing it; prefer
   original explanations and problems where permission is unclear. Treat
   source-derived notes as candidates for human accuracy and rights review.
3. **Choose a broad but bounded first capability slice.** Select a connected
   set of mathematical and physical ideas from the map, define typed inputs,
   units, assumptions, exact or numerical method, limits, checks, and
   conformance tests, then route it through the shared engine. Expand beyond
   constant acceleration when evidence and review are ready.
4. **Review the student release content.** Have the teacher review and correct
   the [constant-acceleration study pack](../products/constant-acceleration-starter-pack.md),
   its worked examples, exercises, answer checks, level, and limitations.
   Record whether it is approved for public use. Keep checkout off meanwhile.
5. **Finish the teacher-to-student lesson workflow.** Add review/export for
   lesson artifacts that preserve source/rights metadata, calculation
   evidence, and reviewer approval. Reuse only reviewed artifacts for students.
6. **Build the first hosted interactive release deliberately.** Choose the
   backend host and deployment architecture. Before accepting student input,
   design authentication if needed, data minimization, retention/deletion,
   privacy notices, access controls, secrets, logging, backups, monitoring,
   incident response, and an operational owner. Keep GitHub Pages as the
   static frontend unless the backend is separately secured.
7. **Prepare the first paid resource only after review.** Confirm rights,
   seller identity, support contact, accessible terms/privacy/refund policies,
   provider accounts, currencies, exact displayed/provider prices, taxes,
   and fulfillment. Test with provider sandbox/test flows before considering
   live checkout.
8. **Grow the learning corpus carefully.** Select one source with explicit
   rights evidence, add a small reviewed batch with provenance, and test
   coverage and answer correctness before adding another topic or exam.
9. **Improve teaching quality and accessibility.** Review explanations with
   subject/teaching expertise; add keyboard, screen-reader, contrast, captions,
   and mobile checks to every student-facing feature.
10. **Continue native and probabilistic work against measured needs.** Add
   capabilities only behind the shared contract and conformance tests. Keep
   probabilistic decisions opt-in with explicit evidence and acceptance checks.
11. **Treat quantum computing as a separate experiment.** Define one reproducible
   research question, classical baseline, resource limits, and benchmark before
   implementing or claiming a quantum advantage. Never route learner data to
   an experiment without explicit approval and safeguards.

## Start the next work session

1. Read this note, the [three-vision build path](./THREE_VISION_BUILD.md),
   [the interface contract](./INTERFACE.md), and the source/right policies in
   [project principles](./PROJECT_PRINCIPLES.md).
2. Build the physics-and-mathematics coverage map before choosing the next
   engine capability. Identify and inspect the relevant user-provided book
   material and MIT OCW sources for the selected areas.
3. Record citations, sections, rights status, and uncertainties; do not copy
   or redistribute source content without permission.
4. Keep payments and public solver endpoints disabled unless their documented
   prerequisites are satisfied.
5. Implement one bounded, tested capability or curriculum slice, and update
   this note as the status changes.
