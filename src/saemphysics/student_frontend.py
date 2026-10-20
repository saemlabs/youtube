import html

from saemphysics.central import StudentResponse
from saemphysics.models import QuestionRecord


TEACHER_CHANNEL_URL = "https://www.youtube.com/@SaemPhysics"


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_student_page(
    questions: list[QuestionRecord],
    selected_question: QuestionRecord | None = None,
    response: StudentResponse | None = None,
    error: str | None = None,
) -> str:
    question_options = "".join(
        '<option value="{question_id}"{selected}>{topic} · {question_id}</option>'.format(
            question_id=_escape(question.question_id),
            topic=_escape(question.topic),
            selected=(
                " selected"
                if selected_question
                and question.question_id == selected_question.question_id
                else ""
            ),
        )
        for question in sorted(questions, key=lambda item: item.question_id)
    )
    feedback = ""
    if error:
        feedback = f'<p class="feedback error" role="alert">{_escape(error)}</p>'
    elif response:
        feedback = (
            f'<p class="feedback {_escape(response.status)}" role="status">'
            f"{_escape(response.message)}</p>"
        )
        if response.next_action:
            feedback += f'<p class="muted">{_escape(response.next_action)}</p>'
        correct_option = (
            response.artifact.get("correct_option")
            if response.artifact
            else None
        )
        if isinstance(correct_option, str):
            feedback += (
                '<p class="answer-reveal">Answer after submission: '
                f"<strong>{_escape(correct_option)}</strong></p>"
            )

    question_panel = ""
    if selected_question:
        if selected_question.options:
            choices = "".join(
                '<label class="choice"><input type="radio" name="selected_option" '
                'value="{key}" required><span><strong>{key}</strong> {text}</span></label>'.format(
                    key=_escape(option.key),
                    text=_escape(option.text),
                )
                for option in selected_question.options
            )
            answer_form = (
                '<form action="/student" method="post">'
                '<input type="hidden" name="action" value="submit_answer">'
                f'<input type="hidden" name="question_id" '
                f'value="{_escape(selected_question.question_id)}">'
                f"{choices}"
                '<button class="button" type="submit">Submit my answer</button>'
                "</form>"
            )
        else:
            answer_form = (
                '<p class="muted">This question does not have answer choices yet; '
                "answer submission is not available.</p>"
            )
        question_panel = (
            '<section class="card" aria-labelledby="active-question">'
            '<p class="eyebrow">YOUR QUESTION</p>'
            f'<h2 id="active-question">{_escape(selected_question.topic)}</h2>'
            f'<p class="question-text">{_escape(selected_question.question_text)}</p>'
            f"{feedback}"
            f"{answer_form}</section>"
        )
    elif feedback:
        question_panel = f'<section class="card">{feedback}</section>'

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#10141b">
    <title>SaemPhysics · Student and teacher</title>
    <link rel="stylesheet" href="/assets/student.css">
    <script src="/assets/student.js" defer></script>
  </head>
  <body>
    <main class="page">
      <header class="topbar">
        <a class="brand" href="/student">SaemPhysics <span>Student space</span></a>
        <nav aria-label="SaemPhysics links">
          <a class="teacher-link" href="/products">Study resources</a>
          <a class="teacher-link" href="{TEACHER_CHANNEL_URL}" target="_blank"
             rel="noopener noreferrer">YouTube ↗</a>
        </nav>
      </header>
      <section class="welcome">
        <p class="eyebrow">LEARN WITH SAEMPHYSICS</p>
        <h1>Ask, practice, understand.</h1>
        <p>Choose a mechanics question, try it yourself, then submit your answer
           for feedback from the shared learning engine.</p>
      </section>
      <section class="card" aria-labelledby="practice-title">
        <p class="eyebrow">START SMALL</p>
        <h2 id="practice-title">Practice one question</h2>
        <form action="/student" method="post">
          <input type="hidden" name="action" value="practice">
          <label for="question-id">Choose a question from the current practice set</label>
          <select id="question-id" name="question_id" required>
            <option value="">Select a question</option>
            {question_options}
          </select>
          <button class="button" type="submit">Open question</button>
        </form>
      </section>
      <section class="card" aria-labelledby="solver-title">
        <p class="eyebrow">VERIFIED MATH TOOLS</p>
        <h2 id="solver-title">Solve and check a calculation</h2>
        <p class="muted">Choose a supported exact operation. The shared processor checks your input and returns its result, verification, and execution trace.</p>
        <form id="student-solver-form">
          <label for="student-operation">Calculation</label>
          <select id="student-operation" name="operation">
            <option value="solve_constant_acceleration">Constant acceleration</option>
            <option value="differentiate">Differentiate an expression</option>
            <option value="definite_integral">Definite integral</option>
            <option value="solve_linear_system">Exact linear system</option>
          </select>
          <div id="student-operation-fields"></div>
          <button class="button" id="student-solve-button" type="submit">Solve and verify</button>
        </form>
        <div id="student-solve-result" aria-live="polite"></div>
      </section>
      {question_panel}
      <footer>
        Python-rendered interface · shared SaemPhysics request processor · local prototype
        <span><a href="/teacher">Teacher lesson studio</a> ·
          <a href="/">Open the full workbench</a></span>
      </footer>
    </main>
  </body>
</html>"""
