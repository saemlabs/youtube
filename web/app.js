"use strict";

const state = {
  questions: [],
  selectedQuestionId: null,
  testQuestions: [],
  testAnswers: new Map(),
};

const byId = (id) => document.getElementById(id);
const make = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

async function api(path, payload) {
  const options = payload === undefined
    ? { headers: { Accept: "application/json" } }
    : {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      };
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function setNotice(message) {
  const notice = byId("notice");
  notice.textContent = message;
  notice.hidden = !message;
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  if (busy) {
    button.dataset.originalLabel = button.textContent;
    button.textContent = label;
  } else if (button.dataset.originalLabel) {
    button.textContent = button.dataset.originalLabel;
    delete button.dataset.originalLabel;
  }
}

function selectedQuestion() {
  return state.questions.find((question) => question.question_id === state.selectedQuestionId);
}

function renderQuestionLibrary() {
  const select = byId("question-select");
  select.replaceChildren();
  for (const question of state.questions) {
    const option = make("option");
    option.value = question.question_id;
    option.textContent = `${question.question_id.slice(-3)} · ${question.topic}`;
    select.append(option);
  }
  if (!state.questions.length) {
    const option = make("option", "", "No questions available");
    option.value = "";
    select.append(option);
    byId("question-preview").replaceChildren(make("p", "muted", "The validated corpus is empty."));
    return;
  }
  state.selectedQuestionId = state.questions[0].question_id;
  select.value = state.selectedQuestionId;
  byId("question-count").textContent = `${state.questions.length} ITEMS`;
  renderQuestionPreview();
}

function renderQuestionPreview() {
  const question = selectedQuestion();
  if (!question) return;
  const preview = byId("question-preview");
  preview.replaceChildren(
    make("p", "", question.question_text),
    make("p", "question-meta", `${question.exam} · ${question.year} · ${question.subject} / ${question.topic}`),
  );
}

async function loadQuestions() {
  setNotice("");
  byId("connection-status").textContent = "Connecting…";
  try {
    const result = await api("/api/questions");
    state.questions = result.questions;
    byId("connection-status").textContent = "Engine connected";
    renderQuestionLibrary();
  } catch (error) {
    byId("connection-status").textContent = "Engine unavailable";
    setNotice(`Could not load the validated question bank. ${error.message}`);
  }
}

async function interact(payload) {
  setNotice("");
  return api("/api/interact", payload);
}

function renderPracticeResult(response) {
  const panel = byId("interaction-result");
  panel.hidden = false;
  panel.replaceChildren();
  const title = make("h3", "", "Practice");
  const status = make("p", "muted", response.message);
  panel.append(title, status);
  if (response.status !== "ready") {
    renderSubmissionFeedback(panel, response);
    return;
  }
  const question = selectedQuestion();
  if (!question) return;
  const prompt = make("p", "", question.question_text);
  panel.append(prompt);
  const choices = make("div", "choice-list");
  let selected = null;
  for (const option of question.options) {
    const choice = make("button", "answer-choice");
    choice.type = "button";
    choice.append(make("span", "choice-key", option.key), make("span", "", option.text));
    choice.addEventListener("click", () => {
      selected = option.key;
      for (const item of choices.children) item.classList.remove("selected");
      choice.classList.add("selected");
      submit.disabled = false;
    });
    choices.append(choice);
  }
  panel.append(choices);
  const submit = make("button", "button button-primary", "Check answer");
  submit.type = "button";
  submit.disabled = true;
  submit.addEventListener("click", async () => {
    setBusy(submit, true, "Checking…");
    try {
      const result = await interact({
        intent: "submit_answer",
        question_id: question.question_id,
        selected_option: selected,
      });
      renderPracticeResult(result);
    } catch (error) {
      setNotice(error.message);
      setBusy(submit, false);
    }
  });
  panel.append(submit);
}

function renderSubmissionFeedback(panel, response) {
  panel.replaceChildren(make("h3", "", response.status === "correct" ? "Correct" : "Answer checked"));
  panel.append(make("p", "muted", response.message));
  if (response.artifact?.correct_option) {
    panel.append(make("p", "", `Correct option: ${response.artifact.correct_option}`));
  }
  if (response.artifact?.derivation_steps) {
    const list = make("ol", "derivation-list");
    for (const step of response.artifact.derivation_steps) list.append(make("li", "", step));
    panel.append(make("h4", "", "Reviewed solution"), list);
  } else if (response.next_action) {
    panel.append(make("p", "muted", response.next_action));
  }
}

async function startPractice() {
  const button = byId("practice-button");
  setBusy(button, true, "Loading…");
  try {
    const response = await interact({ intent: "practice", question_id: state.selectedQuestionId });
    renderPracticeResult(response);
  } catch (error) {
    setNotice(error.message);
  } finally {
    setBusy(button, false);
  }
}

async function startTest() {
  const button = byId("start-test-button");
  setBusy(button, true, "Preparing test…");
  try {
    const response = await interact({
      intent: "start_test",
      question_ids: state.questions.map((question) => question.question_id),
    });
    if (response.status !== "ready") throw new Error(response.message);
    state.testQuestions = response.artifact.questions;
    state.testAnswers = new Map();
    renderTest(response);
  } catch (error) {
    setNotice(error.message);
  } finally {
    setBusy(button, false);
  }
}

function renderTest(response) {
  const panel = byId("interaction-result");
  panel.hidden = false;
  panel.replaceChildren(
    make("h3", "", "Mechanics check-in"),
    make("p", "muted", response.message),
  );
  const form = make("form", "test-form");
  for (const [index, question] of state.testQuestions.entries()) {
    const section = make("fieldset", "test-question");
    section.append(
      make("legend", "eyebrow", `QUESTION ${index + 1} / ${state.testQuestions.length}`),
      make("p", "", question.question_text),
    );
    for (const option of question.options) {
      const label = make("label", "answer-choice");
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `answer-${question.question_id}`;
      input.value = option.key;
      input.required = true;
      input.addEventListener("change", () => state.testAnswers.set(question.question_id, option.key));
      label.append(input, make("span", "choice-key", option.key), make("span", "", option.text));
      section.append(label);
    }
    form.append(section);
  }
  const submit = make("button", "button button-primary", "Submit test");
  submit.type = "submit";
  form.append(submit);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.testAnswers.size !== state.testQuestions.length) return;
    setBusy(submit, true, "Grading…");
    try {
      const response = await interact({
        intent: "submit_test",
        question_ids: state.testQuestions.map((question) => question.question_id),
        answers: Object.fromEntries(state.testAnswers),
      });
      renderTestResults(response);
    } catch (error) {
      setNotice(error.message);
      setBusy(submit, false);
    }
  });
  panel.append(form);
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderTestResults(response) {
  const panel = byId("interaction-result");
  panel.replaceChildren();
  const score = response.artifact;
  const card = make("div", "score-card");
  card.append(
    make("div", "score-number", `${score.percentage}%`),
    make("div", "", ""),
  );
  card.lastElementChild.append(
    make("strong", "", `${score.correct_count} / ${score.total} correct`),
    make("p", "", response.message),
  );
  panel.append(card);
  for (const result of score.results) {
    const item = make("div", "result-line");
    item.append(
      make("span", result.correct ? "result-mark correct" : "result-mark incorrect", result.correct ? "✓" : "×"),
      make("span", "", result.question_id),
      make("span", "muted", `Your answer ${result.selected_option} · correct ${result.correct_option}`),
    );
    if (result.worked_solution) {
      const details = make("details", "solution-details");
      details.append(make("summary", "", `Reviewed solution · ${result.worked_solution.reviewer}`));
      const list = make("ol", "");
      for (const step of result.worked_solution.derivation_steps) list.append(make("li", "", step));
      details.append(list);
      item.append(details);
    }
    panel.append(item);
  }
  if (response.next_action) panel.append(make("p", "muted", response.next_action));
}

function switchView(view) {
  const isLearn = view === "learn";
  byId("learn-view").hidden = !isLearn;
  byId("solve-view").hidden = isLearn;
  byId("page-title").textContent = isLearn ? "Learn & practice" : "Math workbench";
  for (const button of document.querySelectorAll(".nav-link")) {
    button.classList.toggle("active", button.dataset.view === view);
  }
}

function field(label, name, value, type = "text", step = undefined) {
  const wrap = make("div", "");
  const controlId = `input-${name}`;
  const caption = make("label", "field-label", label);
  caption.htmlFor = controlId;
  const input = document.createElement("input");
  input.id = controlId;
  input.name = name;
  input.type = type;
  input.value = value;
  if (step) input.step = step;
  wrap.append(caption, input);
  return wrap;
}

function renderOperationFields() {
  const target = byId("operation-fields");
  const operation = byId("operation-select").value;
  target.replaceChildren();
  if (operation === "solve_constant_acceleration") {
    const grid = make("div", "field-grid");
    grid.append(
      field("Initial velocity u (m/s)", "initial_velocity_m_s", "3"),
      field("Acceleration a (m/s²)", "acceleration_m_s2", "2"),
      field("Time t (s)", "time_s", "4"),
    );
    target.append(grid);
  } else if (operation === "differentiate") {
    target.append(
      field("Expression", "expression", "x**2"),
      field("Variable", "variable", "x"),
    );
  } else if (operation === "definite_integral") {
    const grid = make("div", "field-grid");
    grid.append(
      field("Expression", "expression", "2 + 3*x"),
      field("Variable", "variable", "x"),
      field("Lower bound", "lower_bound", "0"),
      field("Upper bound", "upper_bound", "4"),
    );
    target.append(grid);
  } else {
    const matrixLabel = make("label", "field-label", "Coefficient matrix (one comma-separated row per line)");
    matrixLabel.htmlFor = "input-coefficients";
    const matrix = document.createElement("textarea");
    matrix.id = "input-coefficients";
    matrix.rows = 3;
    matrix.value = "2, 1\n1, 3";
    const rhsLabel = make("label", "field-label", "Right-hand side vector");
    rhsLabel.htmlFor = "input-right-hand-side";
    const rhs = document.createElement("input");
    rhs.id = "input-right-hand-side";
    rhs.value = "5, 6";
    target.append(matrixLabel, matrix, rhsLabel, rhs);
  }
}

function readOperationRequest() {
  const operation = byId("operation-select").value;
  const request = { operation, question_id: "workbench-calculation", numeric_mode: "exact" };
  const value = (name) => byId(`input-${name}`).value.trim();
  if (operation === "solve_constant_acceleration") {
    request.initial_velocity_m_s = value("initial_velocity_m_s");
    request.acceleration_m_s2 = value("acceleration_m_s2");
    request.time_s = value("time_s");
  } else if (operation === "differentiate") {
    request.expression = value("expression");
    request.variable = value("variable");
  } else if (operation === "definite_integral") {
    request.expression = value("expression");
    request.variable = value("variable");
    request.lower_bound = value("lower_bound");
    request.upper_bound = value("upper_bound");
  } else {
    request.coefficients = value("coefficients")
      .split(/\r?\n/)
      .map((row) => row.split(",").map((cell) => cell.trim()));
    request.right_hand_side = value("right_hand_side").split(",").map((cell) => cell.trim());
  }
  return request;
}

function exactNumber(text) {
  const value = String(text);
  if (/^-?\d+\/\d+$/.test(value)) {
    const [numerator, denominator] = value.split("/").map(Number);
    return numerator / denominator;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function renderMotionGraph(result) {
  const u = exactNumber(result.initial_velocity_m_s);
  const a = exactNumber(result.acceleration_m_s2);
  const time = exactNumber(result.time_s);
  if ([u, a, time].some((value) => value === null)) return null;
  const width = 620;
  const height = 190;
  const padding = { left: 52, right: 17, top: 12, bottom: 30 };
  const values = Array.from({ length: 61 }, (_, index) => {
    const t = time * index / 60;
    return { t, s: u * t + 0.5 * a * t * t };
  });
  let min = Math.min(0, ...values.map((point) => point.s));
  let max = Math.max(0, ...values.map((point) => point.s));
  if (max === min) { max += 1; min -= 1; }
  const yPad = (max - min) * 0.12;
  min -= yPad;
  max += yPad;
  const x = (t) => padding.left + (time ? t / time : 0) * (width - padding.left - padding.right);
  const y = (s) => height - padding.bottom - (s - min) / (max - min) * (height - padding.top - padding.bottom);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Displacement versus time curve derived from the exact motion inputs");
  for (let index = 0; index <= 4; index += 1) {
    const fraction = index / 4;
    const gy = padding.top + fraction * (height - padding.top - padding.bottom);
    const value = max - fraction * (max - min);
    const grid = document.createElementNS(svg.namespaceURI, "line");
    grid.setAttribute("x1", padding.left);
    grid.setAttribute("x2", width - padding.right);
    grid.setAttribute("y1", gy);
    grid.setAttribute("y2", gy);
    grid.setAttribute("class", "grid-line");
    svg.append(grid);
    const label = document.createElementNS(svg.namespaceURI, "text");
    label.setAttribute("x", padding.left - 8);
    label.setAttribute("y", gy + 3);
    label.setAttribute("text-anchor", "end");
    label.textContent = Number(value.toPrecision(3)).toString();
    svg.append(label);
  }
  const xAxis = document.createElementNS(svg.namespaceURI, "line");
  xAxis.setAttribute("x1", padding.left);
  xAxis.setAttribute("x2", width - padding.right);
  xAxis.setAttribute("y1", y(0));
  xAxis.setAttribute("y2", y(0));
  xAxis.setAttribute("class", "axis-line");
  svg.append(xAxis);
  const yAxis = document.createElementNS(svg.namespaceURI, "line");
  yAxis.setAttribute("x1", padding.left);
  yAxis.setAttribute("x2", padding.left);
  yAxis.setAttribute("y1", padding.top);
  yAxis.setAttribute("y2", height - padding.bottom);
  yAxis.setAttribute("class", "axis-line");
  svg.append(yAxis);
  const path = document.createElementNS(svg.namespaceURI, "path");
  path.setAttribute("d", values.map((point, index) => `${index ? "L" : "M"} ${x(point.t)} ${y(point.s)}`).join(" "));
  path.setAttribute("class", "curve-line");
  svg.append(path);
  const end = values[values.length - 1];
  const point = document.createElementNS(svg.namespaceURI, "circle");
  point.setAttribute("cx", x(end.t));
  point.setAttribute("cy", y(end.s));
  point.setAttribute("r", "5");
  point.setAttribute("class", "curve-point");
  svg.append(point);
  const xLabel = document.createElementNS(svg.namespaceURI, "text");
  xLabel.setAttribute("x", width - padding.right);
  xLabel.setAttribute("y", height - 7);
  xLabel.setAttribute("text-anchor", "end");
  xLabel.textContent = "time (s)";
  svg.append(xLabel);
  const yLabel = document.createElementNS(svg.namespaceURI, "text");
  yLabel.setAttribute("x", 8);
  yLabel.setAttribute("y", 14);
  yLabel.textContent = "s (m)";
  svg.append(yLabel);
  const figure = make("figure", "motion-figure");
  figure.append(make("figcaption", "", "Displacement over time · s(t) = ut + ½at²"));
  figure.append(svg);
  figure.append(make("p", "fine-print", "Curve shape is a numeric visualization of the exact rational inputs; displayed solver output remains exact."));
  return figure;
}

function renderSolveResult(response, operation) {
  const panel = byId("solve-result");
  panel.replaceChildren();
  if (response.status !== "completed") {
    panel.append(make("p", "notice", response.message));
    return;
  }
  const result = response.artifact.result;
  const heading = make("div", "result-heading");
  const title = make("div", "");
  title.append(make("p", "eyebrow", "COMPUTED OUTPUT"), make("h3", "", "Result"));
  heading.append(title, make("span", "verified-badge", `✓ ${response.verification.status.toUpperCase()}`));
  panel.append(heading);
  const table = make("table", "result-table");
  const body = make("tbody");
  for (const [key, value] of Object.entries(result)) {
    if (key === "checks" || key === "residuals") continue;
    const row = make("tr");
    row.append(make("th", "", key.replaceAll("_", " ")), make("td", "", Array.isArray(value) ? value.join(", ") : String(value)));
    body.append(row);
  }
  table.append(body);
  panel.append(table);
  const checks = response.verification?.checks || [];
  if (checks.length) {
    const checkList = make("div", "checks");
    for (const check of checks) {
      const line = make("div", "check-row");
      line.append(make("span", check.passed ? "check-pass" : "", check.passed ? "✓" : "×"));
      line.append(make("span", "", `${check.name.replaceAll("_", " ")} — ${check.details}`));
      checkList.append(line);
    }
    panel.append(checkList);
  }
  if (operation === "solve_constant_acceleration") {
    const figure = renderMotionGraph(result);
    if (figure) panel.append(figure);
  }
  if (response.trace?.length) {
    const details = make("details", "trace-box");
    details.append(make("summary", "", `Execution trace · ${response.trace.length} layers`));
    const list = make("ul", "trace-list");
    for (const event of response.trace) {
      const item = make("li", "");
      item.append(make("strong", "", event.layer), make("span", "", `${event.event}: ${event.details}`));
      list.append(item);
    }
    details.append(list);
    panel.append(details);
  }
}

async function runCalculation() {
  const button = byId("solve-button");
  const operation = byId("operation-select").value;
  setBusy(button, true, "Computing…");
  setNotice("");
  try {
    const response = await interact({
      intent: "solve",
      calculation: readOperationRequest(),
    });
    renderSolveResult(response, operation);
  } catch (error) {
    byId("solve-result").replaceChildren(make("p", "notice", error.message));
  } finally {
    setBusy(button, false);
  }
}

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});
byId("question-select").addEventListener("change", (event) => {
  state.selectedQuestionId = event.target.value;
  renderQuestionPreview();
});
byId("practice-button").addEventListener("click", startPractice);
byId("refresh-button").addEventListener("click", loadQuestions);
byId("start-test-button").addEventListener("click", startTest);
byId("operation-select").addEventListener("change", renderOperationFields);
byId("solve-button").addEventListener("click", runCalculation);

renderOperationFields();
loadQuestions();
