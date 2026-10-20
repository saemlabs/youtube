#### Build SaemPhysics as an exam-to-visual-explanation engine

## Repository map

- `src/saemphysics/`: typed models, exact solvers, compiler/runtime, and lesson pipeline.
- `tests/`: mathematical, execution, and pipeline checks.
- `examples/`: runnable examples and JSON requests.
- `docs/`: uploaded reference material grouped by topic; see the [document index](./docs/README.md).
- [Phased build roadmap](./docs/ROADMAP.md): monthly milestones and the current first task.
- `prototypes/`: standalone browser prototypes that are not yet connected to the Python pipeline.

Run a structured request through the verified Python backend:

```bash
python -m pip install -e .
saemphysics run examples/requests/constant_acceleration.json
saemphysics validate-sources data/sources.json
saemphysics validate-corpus data/questions
```

Use `-` as the request path to read JSON from standard input. Results are written
as JSON to standard output; invalid requests are reported to standard error with
a nonzero exit status.

The unified student request interface is documented in
[docs/INTERFACE.md](./docs/INTERFACE.md). Try it with
`saemphysics interact examples/requests/student_solve.json`; it routes solve, practice, answer,
explanation, and lesson-draft intents through the capabilities currently
implemented, while clearly marking unsupported work.

## Working foundation

The initial Python vertical slice defines a canonical question record, an exact
constant-acceleration solver, and a verification gate that blocks publication
until both solver checks and human review pass and source rights are cleared.
The sample in `examples/constant_acceleration_demo.py` is synthetic; it is not
an exam question.

The next slice follows the [new architecture paper](./docs/vision/New%20Architecture%20-%20cos%20ai.PDF)'s immediate gap:
machine-independent Semantic IR → Execution IR → capability-checked planning →
an explicit Python-backend Machine IR → execution → verification. Exact rational
inputs remain exact, unsupported approximate execution is rejected, and each
layer emits a trace event. The machine profile is declared by the application;
it is not hardware discovery, native machine code, or a general cognitive
kernel. Architecture v0.1 is a study baseline, not a frozen final design:
future changes should follow further source study and tested architectural
revisions rather than implementing every long-term layer at once.

The lesson compiler adds versioned, renderer-independent scene plans with
question/source field references, a learning objective, narration cues,
visual actions, assumptions, derivation steps, and verification checks. It
accepts only verified solutions, creates drafts rather than approved lessons,
and preserves the separate human-review and source-rights publication gates.
The first optional renderer example is a short Manim scene for the synthetic
constant-acceleration lesson. Its motion model is independently testable and
accepts only solver results that passed verification; the scene is still a
preview, not an approved lesson or publication.

## Mathematical working layer

The newly added mathematics tools turn three study principles into executable
behavior:

- Feynman's computation-first approach: build a small mechanism, make each
  layer's job visible, and distinguish what can be computed from what is
  efficient or physically feasible. The current Python backend is not a claim
  of hardware-independent execution.
- Gilbert Strang's applied linear algebra: treat a matrix as an operator on
  meaningful vectors, not merely a table of numbers. `solve_linear_system`
  solves exact, square, nonsingular systems and checks the residual `A*x - b`;
  it does not yet exploit sparse or specially structured matrices.
- Calculus as connected models of change and accumulation: `differentiate`
  checks symbolic rates; `definite_integral` checks a finite result against
  antiderivative and endpoint evaluation on an interval established as
  continuous.
- The programming references' modularity and testing principles: math
  functions are isolated from rendering, unsupported syntax fails explicitly,
  and known results and failure cases are tested.

These tools use a small AST-based arithmetic grammar rather than Python `eval`
or unrestricted symbolic parsing. Inputs and outputs remain exact whenever
the operation permits it. This is a tested math-library slice, not yet a new
general computer algebra system, numerical ODE engine, or automatic lesson
generator. Differentiation, definite integration, and exact linear-system
solves now run through Semantic IR → Execution IR → the registered Python
backend → checks, alongside the original constant-acceleration operation.
`attach_verified_solution` connects a passing execution to its matching
sourced question, requires explicit derivation text, and preserves check
evidence for lesson compilation. The resulting lesson remains a draft; human
question/lesson review and source-rights checks still control publication.

Try the calculus/linear-algebra example:

```bash
python examples/mathematics_demo.py
```

The synthetic motion example shows the larger question → compiled solve →
verified solution attachment → sourced lesson-draft flow. Replace its
hand-authored teaching derivation with a teacher-reviewed explanation for real
content; computed results do not generate or approve pedagogy.

The implementation is informed by the uploaded computation, mathematical,
physics, and programming references. They are now grouped in the [document
index](./docs/README.md), which links to every source file and distinguishes
the current design references from material reserved for later study. The
quantum-algorithm material does not justify adding a quantum backend before
the ordinary math path is validated. The 14-page
[`algorithm for quantum computing.pdf`](./docs/quantum/algorithm%20for%20quantum%20computing.pdf)
is image-only with no extractable text, so its contents were not used as
implementation requirements.

Set up and run the prototype with Python 3.10 or newer:

```bash
python -m pip install -e ".[dev]"
pytest
python examples/constant_acceleration_demo.py
```

To render the optional animation, install Manim's system dependencies using
the [official installation guide](https://docs.manim.community/en/stable/installation.html),
then install the animation extra and render the low-quality preview:

```bash
python -m pip install -e ".[dev,animation]"
python -m manim -ql examples/constant_acceleration_scene.py ConstantAccelerationLesson
```

The scene uses ordinary text and geometric objects, not LaTeX-rendered
equations. Rendering still requires Manim's supported system libraries and
FFmpeg. Inspect the preview at normal speed; a successful render does not
replace physics, visual, or human review.

The existing [Exam Forecaster](./prototypes/Exam%20Forecaster%201.html) and
[Mock Tester](./prototypes/Mock%20Tester%201.html) remain standalone browser
prototypes. This foundation does not yet connect them to the Python pipeline.

Your goal is bigger than an AI that solves NEET, JEE, MIT, and Olympiad questions. You want a system that understands 30 years of exam questions, identifies the underlying mathematical and physical ideas, verifies the answer independently, and turns the reasoning into a 3Blue1Brown-inspired visual lesson.

The key is to build this as a tested Python application in GitHub Codespaces, not as one giant prompt to Gemini or DeepSeek.

The core principle:

> AI proposes the explanation. Your mathematics and physics engines verify the solution. Your teaching engine turns the verified reasoning into an original visual lesson.

### 1\. The architecture you should build

1\. Exam question library

NEET · JEE Main · JEE Advanced · MIT exams · Olympiads

Question, year, exam, subject, source, diagram, answer key, licence

2\. Question understanding

OCR · equations · diagrams · units · answer choices

3\. Concept and thinker mapping

Concept graph · prerequisites · Feynman-inspired intuition · alternative solution paths

4A. Maths engine

SymPy, numerical checks, dimensions, limiting cases

4B. Physics engine

Equations of motion, conservation laws, fields, circuits, simulations

5\. Independent verification gate

Symbolic result · numerical result · units · assumptions · answer-key comparison

Unverified questions cannot be published automatically

6\. Visual lecture compiler

Conceptual hook → derivation → animated geometry → experiment/simulation → exam shortcut → recap

Manim · Python · narration · captions · video rendering

The important design decision is to make every stage save a structured artifact. If the visual explanation is wrong, you should be able to trace the issue back to the question interpretation, concept mapping, derivation, or animation—not start from scratch.

### 2\. Start in GitHub Codespaces

Don't ingest all 30 years at the beginning. First build a working prototype for 20–50 questions from one topic, such as Newton's laws or electrostatics. Prove the complete pipeline on those questions, then scale it.

### Step 1 — Create the repository

Create a private repository called `saemphysics-engine` on GitHub and open it in Codespaces.

Choose a Python development container. In the Codespaces terminal, run:

```bash
mkdir -p data/raw data/processed data/questions
mkdir -p src/ingestion src/concepts src/solvers
mkdir -p src/verification src/teaching src/visuals
mkdir -p tests notebooks docs

touch src/__init__.py
touch src/ingestion/__init__.py
touch src/concepts/__init__.py
touch src/solvers/__init__.py
touch src/verification/__init__.py
touch src/teaching/__init__.py
touch src/visuals/__init__.py

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install sympy numpy scipy pint pydantic pytest jupyter
pip install manim
```

If Manim installation fails because of system dependencies, keep developing the question and solver pipeline first; add Manim through a compatible development-container configuration later. You do not need a GPU to build the initial symbolic solver.

Create a `requirements.txt` after validating the environment:

```bash
pip freeze > requirements.txt
```

Use a pinned, tested dependency set for reproducible builds rather than treating the output of `pip freeze` as a permanent universal requirements file.

### Step 2 — Use this repository structure

### saemphysics-engine/

data/raw/

Original documents you are authorized to process; keep immutable.

data/processed/

OCR text, extracted equations, diagrams and normalized data.

data/questions/

Canonical question records in JSON or JSONL.

src/ingestion/

PDF parsing, OCR, diagram extraction and source tracking.

src/concepts/

Concept taxonomy, prerequisite graph and thinker-inspired teaching principles.

src/solvers/

Symbolic mathematics, numerical methods and physics solvers.

src/verification/

Independent checks, unit checks and confidence status.

src/teaching/

Explanation plans, derivation steps and exam strategies.

src/visuals/
Renderer-independent visual models and renderer-specific scene examples built
from verified physics results.

tests/

Known answers, edge cases, regressions and scientific checks.

docs/

Design decisions, source policy and teaching standards.

Add a `pyproject.toml` or equivalent project configuration, a `.gitignore`, and a `README.md`. Keep original exam PDFs out of Git if they are large, restricted, or not licensed for redistribution. Use a manifest that records their source and local file location instead.

### 3\. Build a canonical question record

This is the most important data-design decision. Different exam papers must be converted into the same internal format without losing their original context.

For example, create `data/questions/example.json`:

```json
{
  "question_id": "jee_advanced_2024_physics_001",
  "exam": "JEE Advanced",
  "year": 2024,
  "subject": "physics",
  "topic": "mechanics",
  "subtopic": "work_energy",
  "language": "en",
  "source": {
    "document_id": "jee_advanced_2024_paper_1",
    "page": 3,
    "question_number": "1",
    "url": null,
    "rights_status": "review_required"
  },
  "question_text": "Insert the verified question text here.",
  "diagram_assets": [],
  "options": [],
  "official_answer": null,
  "concepts": [],
  "solution": {
    "status": "not_solved",
    "assumptions": [],
    "derivation_steps": [],
    "symbolic_result": null,
    "numerical_result": null,
    "units": null,
    "verification_checks": []
  },
  "teaching_plan": {
    "intuition": null,
    "visual_analogy": null,
    "common_misconception": null,
    "exam_strategy": null
  },
  "review": {
    "human_verified": false,
    "reviewer": null
  }
}
```

This is a schema example, not a real exam question. Populate the record only from a source you have actually checked.

Keep these three things separate:

* Official answer: what the source's answer key says, with its provenance.

* Computed answer: what your solver derives.

* Reviewed answer: what a human has checked and approved.

If these disagree, mark the question for review. Do not silently change the official answer or let an AI model declare itself correct.

### 4\. Create a concept graph, not just topic tags

A simple tag such as `work_energy` is useful, but not enough to teach like a great physicist. The system needs to understand which ideas depend on which other ideas.

For example:

Vectors and components

Force and displacement

Work and kinetic energy

Conservation of mechanical energy

Exam problem → verified derivation → animated explanation

Each question can map to multiple concepts, prerequisite concepts, common misconceptions, and solution methods.

Your “Feynman layer” should encode teaching moves, not imitate a person's exact voice. For example:

* Start with a physical question the student can picture.

* Identify the mechanism before introducing equations.

* Explain what each term means physically.

* Use a limiting case to test intuition.

* Show how a general principle simplifies the exam problem.

You can add other documented intellectual influences as teaching frameworks: mathematical structure, experimental reasoning, symmetry, computation, or dimensional analysis. Keep historical attribution factual and make the actual explanations original.

### 5\. Build the maths and physics engines before the AI lecture generator

Your engine needs to distinguish between problems that can be solved exactly, problems that need numerical methods, and problems that require physical interpretation.

### A. Mathematics engine

Use:

* SymPy for symbolic algebra, equation solving, differentiation, integration and simplification.

* NumPy/SciPy for numerical calculations, simulations and numerical equation solving.

* Pint for physical units.

* pytest for regression tests.

Create `src/solvers/math_engine.py`:

```python
import sympy as sp

def solve_equation(equation, variable):
    """Return symbolic solutions and the equation used."""
    solutions = sp.solve(equation, variable)

    return {
        "equation": str(equation),
        "variable": str(variable),
        "solutions": [sp.sstr(s) for s in solutions],
    }

if __name__ == "__main__":
    x = sp.symbols("x", real=True)
    equation = sp.Eq(x**2 - 5*x + 6, 0)

    print(solve_equation(equation, x))
```

Run it:

```bash
python src/solvers/math_engine.py
```

Expected solutions are and .

This is only a basic symbolic-solver demonstration. The production engine must also check domain restrictions, extraneous roots, singularities and whether all solutions satisfy the original problem.

### B. Physics engine

Do not begin with a single universal “physics AI.” Create small, testable domain solvers:

| Module            | Initial responsibility                           |
| ----------------- | ------------------------------------------------ |
| mechanics.py      | Kinematics, Newton's laws, work-energy, momentum |
| electrostatics.py | Coulomb's law, electric fields and potentials    |
| circuits.py       | Kirchhoff laws, resistor networks, RC circuits   |
| waves.py          | Oscillations, superposition and wave relations   |
| thermodynamics.py | Ideal-gas relations, energy balances             |
| optics.py         | Ray geometry, lenses and interference            |

Each solver should state its assumptions. For example, a constant-acceleration solver must not silently apply its equations to arbitrary time-varying acceleration.

The verification layer should check:

* Whether the derivation follows the stated assumptions.

* Whether the result satisfies the original equations.

* Whether dimensions and units are consistent.

* Whether the result behaves sensibly in limiting cases.

* Whether an independent method agrees, when available.

* Whether the official answer agrees, where a reliable key exists.

Important: dimensional analysis and a matching answer choice are useful checks, but neither proves that a derivation is correct.

### 6\. The visual engine should consume verified solutions

Use Manim Community for mathematical animations. Do not ask a language model to produce an entire polished video in one generation.

Instead, ask it to produce a structured storyboard that your code can validate.

Example `teaching_plan.json`:

```json
{
  "question_id": "your_question_id",
  "verification_status": "human_verified",
  "scenes": [
    {
      "type": "physical_intuition",
      "purpose": "Establish what is happening physically"
    },
    {
      "type": "diagram",
      "purpose": "Show the relevant objects and vectors"
    },
    {
      "type": "derivation",
      "purpose": "Explain each mathematical step"
    },
    {
      "type": "simulation",
      "purpose": "Test the relationship visually"
    },
    {
      "type": "exam_strategy",
      "purpose": "Connect the principle to the shortest valid solution"
    }
  ]
}
```

Treat this as a proposed storyboard format. Your application should validate it against a schema, populate the scenes with the actual verified equations, and reject unsupported claims.

A reliable production flow is:

* The AI drafts the intuitive explanation.

* The concept graph supplies prerequisites and misconceptions.

* The solver supplies the approved equations and results.

* A scene planner selects visual elements.

* Manim renders the animation.

* A separate review checks the visuals against the derivation.

* Narration, captions and editing are added after the scientific content passes review.

This gives you the clarity and visual pedagogy you admire in 3Blue1Brown while developing your own visual identity and teaching style.

### 7\. How to integrate Gemini and DeepSeek

Keep AI providers behind a common interface. This lets you change models without rewriting your engine.

For example, create `src/teaching/ai_client.py` with a function conceptually like:

```python
def generate_explanation(question, concepts, verified_solution):
    """
    Ask the selected AI provider for an explanation plan.

    Inputs:
      - normalized question
      - retrieved concept records
      - verified solution and assumptions

    Output:
      - structured explanation plan
      - suggested visualizations
      - cited source records
    """
    raise NotImplementedError
```

Implement the provider using the appropriate official API or SDK, with API keys stored in Codespaces secrets or environment variables—not in source code or committed notebooks.

Give the model the verified solution and ask it to explain that solution. Do not let it invent numerical answers, silently change assumptions, or treat a retrieved answer key as proof.

You can use different models for different tasks:

* One for question classification and concept mapping.

* Another for generating alternative derivations or explanations.

* Deterministic code for symbolic and numerical checks.

* A human reviewer for unresolved disagreements and final approval.

AI agreement is not independent mathematical verification: two models can make the same mistake.

### 8\. How to scale to 30 years of questions

Build the corpus in stages.

* Pilot: 20–50 questions from one topic, manually checked.

* Topic expansion: 200–500 questions covering multiple difficulty levels and solution types.

* Exam expansion: ingest papers year by year, with source provenance and automated quality checks.

* Concept analytics: measure topic frequency, prerequisite gaps, recurring misconceptions and alternative solution methods.

* Lecture generation: group questions into coherent lessons instead of producing one disconnected video per question.

For ingestion, preserve the original document and page reference, OCR confidence, diagram references, answer-key provenance and rights status. OCR output should never be treated as authoritative until equations, signs, exponents and diagrams have been checked.

For MIT material, review the licence of each course and asset. Exam questions may have different rights from lecture notes. Store references and metadata when redistribution rights are unclear, and generate original explanations rather than copying lecture wording or animations.

### 9\. Your first 30 days in Codespaces

### 30-day build checklist

0/12

Week 1 — Build the foundation

Create the repository and Python environment

Create the question JSON schema

Add 20 manually verified questions from one topic

Week 2 — Verify solutions

Implement a SymPy solver for the chosen topic

Add unit, limiting-case and regression tests

Record official-answer versus computed-answer disagreements

Week 3 — Connect teaching to verification

Create a small concept graph

Generate structured explanation plans

Reject unverified or incomplete solution records

Week 4 — Produce the first visual lesson

Build reusable Manim scene templates

Render one complete question explanation

Review scientific accuracy and publish only after checking

Copy checklist

### 10\. The strategic decision that matters most

Do not measure the success of this engine by how many PDFs it has ingested. Measure it by how many questions it can solve correctly, explain clearly, trace to trustworthy sources, and turn into scientifically accurate lessons.

Start with a single topic and build a vertical slice:

One source paper → one normalized question → one verified solution → one concept map → one excellent animation.

Once that works reliably, expanding to thousands of questions becomes a data and engineering problem rather than an uncontrolled AI experiment.

One question will help determine the best first implementation: Which question bank should we integrate first?

1\. Starting question bank

NEET

JEE Main

JEE Advanced

MIT exams / Olympiads

Mixed corpus

2\. First topic

Mechanics

Electrostatics

Calculus and mathematical methods

Mixed topics

3\. Where the papers are

PDF papers I already have

Official online sources

A spreadsheet or question database

Not collected yet

Design my first runnable prototype

PDF papers I already have

Official online sources

A spreadsheet or question database

Not collected yet
