"use strict";

const get = (id) => document.getElementById(id);

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function inputField(container, labelText, name, value) {
  const wrapper = element("div");
  const label = element("label", labelText);
  const input = element("input");
  input.id = `student-${name}`;
  input.name = name;
  input.value = value;
  input.required = true;
  label.htmlFor = input.id;
  wrapper.append(label, input);
  container.append(wrapper);
}

function renderFields() {
  const target = get("student-operation-fields");
  target.replaceChildren();
  const operation = get("student-operation").value;
  if (operation === "solve_constant_acceleration") {
    const grid = element("div");
    grid.className = "input-grid";
    inputField(grid, "Initial velocity u (m/s)", "initial_velocity_m_s", "3");
    inputField(grid, "Acceleration a (m/s²)", "acceleration_m_s2", "2");
    inputField(grid, "Time t (s)", "time_s", "4");
    target.append(grid);
  } else if (operation === "differentiate") {
    inputField(target, "Expression", "expression", "x**2");
    inputField(target, "Variable", "variable", "x");
  } else if (operation === "definite_integral") {
    inputField(target, "Expression", "expression", "2 + 3*x");
    inputField(target, "Variable", "variable", "x");
    const grid = element("div");
    grid.className = "input-grid";
    inputField(grid, "Lower bound", "lower_bound", "0");
    inputField(grid, "Upper bound", "upper_bound", "4");
    target.append(grid);
  } else {
    const matrixLabel = element(
      "label",
      "Coefficient matrix (comma-separated rows)"
    );
    const matrix = element("textarea");
    matrix.id = "student-coefficients";
    matrix.name = "coefficients";
    matrix.rows = 3;
    matrix.value = "2, 1\n1, -1";
    matrix.required = true;
    matrixLabel.htmlFor = matrix.id;
    const rhsLabel = element("label", "Right-hand side vector (comma-separated)");
    const rhs = element("input");
    rhs.id = "student-right-hand-side";
    rhs.name = "right_hand_side";
    rhs.value = "5, 1";
    rhs.required = true;
    rhsLabel.htmlFor = rhs.id;
    target.append(matrixLabel, matrix, rhsLabel, rhs);
  }
}

function calculationFromForm() {
  const operation = get("student-operation").value;
  const calculation = {
    operation,
    question_id: "student-workbench-calculation",
    numeric_mode: "exact",
  };
  const value = (name) => get(`student-${name}`).value.trim();
  if (operation === "solve_constant_acceleration") {
    calculation.initial_velocity_m_s = value("initial_velocity_m_s");
    calculation.acceleration_m_s2 = value("acceleration_m_s2");
    calculation.time_s = value("time_s");
  } else if (operation === "differentiate") {
    calculation.expression = value("expression");
    calculation.variable = value("variable");
  } else if (operation === "definite_integral") {
    calculation.expression = value("expression");
    calculation.variable = value("variable");
    calculation.lower_bound = value("lower_bound");
    calculation.upper_bound = value("upper_bound");
  } else {
    calculation.coefficients = value("coefficients")
      .split(/\r?\n/)
      .map((row) => row.split(",").map((cell) => cell.trim()));
    calculation.right_hand_side = value("right_hand_side")
      .split(",")
      .map((cell) => cell.trim());
  }
  return calculation;
}

function renderResult(response) {
  const target = get("student-solve-result");
  target.replaceChildren();
  if (response.status !== "completed" || !response.artifact?.result) {
    target.append(element("p", response.message || "The calculation was not completed."));
    return;
  }

  target.append(
    element("h3", "Result"),
    element("p", `Verification: ${response.verification?.status || "unavailable"}`)
  );
  const result = response.artifact.result;
  const list = element("dl");
  for (const [name, value] of Object.entries(result)) {
    if (name === "checks") continue;
    const term = element("dt", name.replaceAll("_", " "));
    const description = element(
      "dd",
      Array.isArray(value) ? value.join(", ") : String(value)
    );
    list.append(term, description);
  }
  target.append(list);

  const checks = response.verification?.checks || [];
  if (checks.length) {
    const heading = element("h4", "Verification checks");
    const items = element("ul");
    for (const check of checks) {
      items.append(
        element(
          "li",
          `${check.passed ? "Passed" : "Failed"} — ${check.name}: ${check.details}`
        )
      );
    }
    target.append(heading, items);
  }
  if (response.trace?.length) {
    const details = element("details");
    details.append(element("summary", "Execution trace"));
    const items = element("ol");
    for (const event of response.trace) {
      items.append(
        element("li", `${event.layer}: ${event.event} — ${event.details}`)
      );
    }
    details.append(items);
    target.append(details);
  }
}

async function submitCalculation(event) {
  event.preventDefault();
  const button = get("student-solve-button");
  const target = get("student-solve-result");
  button.disabled = true;
  target.replaceChildren(element("p", "Solving and verifying…"));
  try {
    const response = await fetch("/api/interact", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        intent: "solve",
        calculation: calculationFromForm(),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    renderResult(payload);
  } catch (error) {
    target.replaceChildren(element("p", error.message));
  } finally {
    button.disabled = false;
  }
}

get("student-operation").addEventListener("change", renderFields);
get("student-solver-form").addEventListener("submit", submitCalculation);
renderFields();
