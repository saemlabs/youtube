# One build path for the three SaemPhysics visions

The three visions are related outcomes of one learning engine, not three
separate products to build in parallel:

1. **Quantum cognitive operating system** — the long-term research direction:
   a transparent, composable system of typed capabilities, evidence, memory,
   and explicit decision boundaries, with carefully scoped future experiments
   on quantum-computing platforms.
2. **Saem EdTech platform** — the learner and teacher product: practice,
   assessment, explanations, progress, and reviewed learning resources.
3. **Daily SaemPhysics teaching content** — the creator workflow: turn a
   supported subject or problem into a correct, teachable lesson draft, then
   have the teacher review and adapt it for students and the
   [SaemPhysics YouTube channel](https://www.youtube.com/@SaemPhysics).

## The unifying model

Every user-facing workflow should share the same progression:

```text
teacher or learner intent
    -> validated request
    -> registered capability
    -> result + verification + trace + source provenance
    -> reviewable draft or learner response
    -> human decision before publication or high-trust use
```

This is the current architecture in small form: the student request contract,
central processor, exact math runtime, question/source models, and lesson draft
compiler. Each new capability should strengthen this shared path instead of
creating a separate content generator, platform backend, or cognitive engine.

## Build order: one vertical slice at a time

### 1. Make one useful teacher lesson end to end

Start with an original, narrow mechanics example such as the existing synthetic
constant-acceleration pilot. The teacher workflow should:

- identify the topic, audience, learning objective, and what students should
  already know;
- use an original or rights-cleared question with preserved source metadata;
- run only a supported calculation and retain exact inputs, output,
  verification checks, and execution trace;
- produce a structured lesson/storyboard draft with claims linked to their
  evidence;
- leave narration, diagrams, teaching emphasis, and publication under teacher
  review; never imply that a draft is already a finished or approved video.

**Exit evidence:** one runnable original lesson artifact that can be inspected,
checked, and adapted by the teacher, with verification and review blockers
visible.

### 2. Reuse the same artifact in the EdTech learner flow

Use that reviewed lesson and its question record in practice and assessment.
Learners should get the same checked result and teaching explanation that the
teacher reviewed; grading and solution visibility must continue to use the
central processor and existing review gates.

**Exit evidence:** one learner can practice a question, submit an answer, and
receive appropriate feedback tied to the same reviewed content and provenance.
Add persistence only after privacy, consent, retention, and deletion choices
are settled.

### 3. Add cognitive structure only where it improves the learning loop

Introduce versioned concepts, prerequisites, misconception signals, and
learner-progress evidence in small, inspectable steps. Keep observations
distinct from inferences and recommendations; show the evidence and allow a
teacher or learner to correct them.

**Exit evidence:** a small reviewed concept graph supports an actual practice
or teaching decision, with tests for invalid links and cycles.

### 4. Establish the cognitive-OS and quantum research boundary

Keep capabilities typed, bounded, traceable, deterministic where possible,
and replaceable behind the versioned contract. Treat memory, planning,
adaptation, and quantum execution as separate capabilities with explicit
resource and trust limits. Begin quantum work as offline, reproducible
research experiments; do not route learner data to a quantum service or claim
quantum advantage without a documented benchmark.

**Exit evidence:** one scoped experiment with a classical baseline, stated
assumptions, resource limits, repeatable results, and an honest account of
whether the quantum component adds value.

## Shared acceptance checks

Every vertical slice should answer:

- Is the request schema explicit, bounded, and shared across interfaces?
- Can the student or teacher inspect the result, verification, trace, and
  relevant source lineage?
- Are computed facts separated from teaching interpretation and model
  suggestions?
- Are rights, privacy, and human-review blockers represented rather than
  silently assumed away?
- Does a test prove both the supported path and important failure cases?
- Can this capability be reused by the other two visions without duplicating
  trust rules?

## Current next step

The student/teacher shell, request processor, exact math path, lesson schema,
cross-language contract vectors, a versioned three-concept graph, and
opt-in C, C++, and C# constant-acceleration capabilities with a cross-checked
Python adapter are present. The local
`/teacher` studio connects one original
constant-acceleration problem to the verified lesson draft compiler and
displays the scenes, checks, trace, and review/rights blockers. It remains
stateless and does not render or publish video. The next step is a teacher
review/export workflow for this same artifact, without introducing learner-data
persistence or external content before rights and privacy requirements are
settled. The concept graph is structural draft metadata until a qualified
reviewer approves it.
