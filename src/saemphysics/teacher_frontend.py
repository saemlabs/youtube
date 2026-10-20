import html

from saemphysics.central import StudentResponse
from saemphysics.teacher_workflow import TeacherLessonInput


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _field_value(
    values: TeacherLessonInput | None,
    name: str,
) -> str:
    if values is None:
        return ""
    return _escape(getattr(values, name) or "")


def render_teacher_page(
    response: StudentResponse | None = None,
    values: TeacherLessonInput | None = None,
    error: str | None = None,
) -> str:
    question_text = _field_value(values, "question_text")
    initial_velocity = _field_value(values, "initial_velocity_m_s")
    acceleration = _field_value(values, "acceleration_m_s2")
    time = _field_value(values, "time_s")
    intuition = _field_value(values, "intuition")
    misconception = _field_value(values, "common_misconception")

    feedback = ""
    if error:
        feedback = f'<p class="feedback error" role="alert">{_escape(error)}</p>'
    elif response:
        feedback = (
            f'<p class="feedback {_escape(response.status)}" role="status">'
            f"{_escape(response.message)}</p>"
        )

    artifact = response.artifact if response else None
    lesson = artifact.get("lesson") if artifact else None
    scenes = lesson.get("scenes", []) if isinstance(lesson, dict) else []
    scene_cards = "".join(
        (
            '<article class="scene-card">'
            f'<p class="eyebrow">{_escape(scene.get("role", "scene"))}</p>'
            f'<h3>{_escape(scene.get("scene_id", "Lesson scene"))}</h3>'
            f'<p><strong>Purpose:</strong> {_escape(scene.get("teaching_purpose", ""))}</p>'
            f'<p><strong>Narration cue:</strong> {_escape(scene.get("narration_cue", ""))}</p>'
            f'<p><strong>Visual:</strong> {_escape(scene.get("visual_action", ""))}</p>'
            f'<p><strong>Learner takeaway:</strong> {_escape(scene.get("learner_inference", ""))}</p>'
            + (
                "<ul>"
                + "".join(f"<li>{_escape(item)}</li>" for item in scene["equations"])
                + "</ul>"
                if scene.get("equations")
                else ""
            )
            + "</article>"
        )
        for scene in scenes
        if isinstance(scene, dict)
    )

    checks = (
        response.verification.get("checks", [])
        if response and response.verification
        else []
    )
    check_items = "".join(
        '<li class="{status}"><strong>{name}</strong> — {details}</li>'.format(
            status="passed" if check.get("passed") else "failed",
            name=_escape(check.get("name", "check")),
            details=_escape(check.get("details", "")),
        )
        for check in checks
        if isinstance(check, dict)
    )
    blockers = (
        artifact.get("publication", {}).get("blockers", [])
        if artifact and isinstance(artifact.get("publication"), dict)
        else []
    )
    blocker_items = "".join(f"<li>{_escape(blocker)}</li>" for blocker in blockers)
    trace = response.trace if response else []
    trace_items = "".join(
        "<li><strong>{layer}</strong>: {event} — {details}</li>".format(
            layer=_escape(event.get("layer", "")),
            event=_escape(event.get("event", "")),
            details=_escape(event.get("details", "")),
        )
        for event in trace
        if isinstance(event, dict)
    )

    result_section = ""
    if response:
        result_section = f"""
      <section class="card" aria-labelledby="draft-heading">
        <p class="eyebrow">TEACHER REVIEW REQUIRED</p>
        <h2 id="draft-heading">Lesson draft</h2>
        {feedback}
        <p class="muted">This is a reviewable outline, not a finished or approved video.
           It is not saved between requests.</p>
        <h3>Computation verification</h3>
        <ul class="checks">{check_items}</ul>
        <h3>Publication blockers</h3>
        <ul>{blocker_items}</ul>
        <h3>Execution trace</h3>
        <ol class="trace">{trace_items}</ol>
        <div class="scene-list">{scene_cards}</div>
      </section>
"""
    elif error:
        result_section = f'<section class="card">{feedback}</section>'

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#10141b">
    <title>SaemPhysics · Teacher lesson studio</title>
    <link rel="stylesheet" href="/assets/student.css">
  </head>
  <body>
    <main class="page">
      <header class="topbar">
        <a class="brand" href="/teacher">SaemPhysics <span>Teacher studio</span></a>
        <a class="teacher-link" href="https://www.youtube.com/@SaemPhysics"
           target="_blank" rel="noopener noreferrer">Your YouTube channel ↗</a>
      </header>
      <section class="welcome">
        <p class="eyebrow">CREATE DAILY TEACHING CONTENT</p>
        <h1>Start with one verified example.</h1>
        <p>Enter an original constant-acceleration problem and its exact values.
           The shared engine checks the calculation and prepares a lesson outline
           for your review.</p>
      </section>
      <section class="card" aria-labelledby="lesson-input-heading">
        <p class="eyebrow">ORIGINAL TEACHER DRAFT</p>
        <h2 id="lesson-input-heading">Problem and teaching focus</h2>
        <form action="/teacher" method="post">
          <input type="hidden" name="action" value="create_lesson">
          <label for="question-text">Problem statement (ensure it matches the values below)</label>
          <textarea id="question-text" name="question_text" rows="3" maxlength="2000"
                    required>{question_text}</textarea>
          <div class="input-grid">
            <div><label for="initial-velocity">Initial velocity (m/s)</label>
              <input id="initial-velocity" name="initial_velocity_m_s" value="{initial_velocity}"
                     maxlength="64" required></div>
            <div><label for="acceleration">Acceleration (m/s²)</label>
              <input id="acceleration" name="acceleration_m_s2" value="{acceleration}"
                     maxlength="64" required></div>
            <div><label for="time">Time (s)</label>
              <input id="time" name="time_s" value="{time}" maxlength="64" required></div>
          </div>
          <label for="intuition">Your physical intuition (optional)</label>
          <textarea id="intuition" name="intuition" rows="2" maxlength="500">{intuition}</textarea>
          <label for="misconception">Common misconception to address (optional)</label>
          <textarea id="misconception" name="common_misconception" rows="2"
                    maxlength="500">{misconception}</textarea>
          <button class="button" type="submit">Verify and draft lesson</button>
        </form>
      </section>
      {result_section}
      <footer>
        Local-only draft · exact calculation uses the shared engine · review before teaching or publishing
        <span><a href="/student">Student space</a> · <a href="/">Full workbench</a></span>
      </footer>
    </main>
  </body>
</html>"""
