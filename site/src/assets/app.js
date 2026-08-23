const CONTROL_ORDER = ["freshness", "uncertainty", "risk", "conflict", "budget", "goal"];
const OUTPUT_FIELDS = [
  "disposition",
  "reason_key",
  "effective_fact_status",
  "selected_channel",
  "budget_before",
  "projected_budget_after",
  "affordable",
  "action_readiness",
];
const ROW_FIELDS = [
  "scenario_key",
  "disposition",
  "reason_key",
  "effective_fact_status",
  "selected_channel",
  "expected_gain",
  "estimated_cost",
  "budget_before",
  "projected_budget_after",
  "affordable",
  "action_readiness",
  "facts_to_verify",
  "blocking_facts",
];

document.documentElement.dataset.site = "apr";

export function scenarioKey(state) {
  return CONTROL_ORDER.map((name) => state[name]).join(":");
}

export function renderScenario(output, row, labels) {
  const list = document.createElement("dl");
  for (const field of OUTPUT_FIELDS) {
    const term = document.createElement("dt");
    term.textContent = labels[field];
    const detail = document.createElement("dd");
    detail.textContent = String(row[field]);
    list.append(term, detail);
  }
  output.replaceChildren(list);
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function validatePayload(payload) {
  if (
    !isRecord(payload) ||
    payload.schema !== "apr-demo-scenarios/v1" ||
    !Array.isArray(payload.controls) ||
    payload.controls.length !== CONTROL_ORDER.length ||
    !payload.controls.every((name, index) => name === CONTROL_ORDER[index]) ||
    !isRecord(payload.scenarios)
  ) {
    throw new Error("Invalid APR demo scenario payload");
  }

  for (const [key, row] of Object.entries(payload.scenarios)) {
    if (
      !isRecord(row) ||
      Object.keys(row).length !== ROW_FIELDS.length ||
      !ROW_FIELDS.every((field) => Object.hasOwn(row, field)) ||
      row.scenario_key !== key
    ) {
      throw new Error("Invalid APR demo scenario row");
    }
  }
  return payload.scenarios;
}

function readState(form) {
  const formData = new FormData(form);
  return Object.fromEntries(CONTROL_ORDER.map((name) => [name, formData.get(name)]));
}

function outputLabels(form) {
  return Object.fromEntries(
    OUTPUT_FIELDS.map((field) => {
      const dataName = `label${field
        .split("_")
        .map((part) => part[0].toUpperCase() + part.slice(1))
        .join("")}`;
      return [field, form.dataset[dataName]];
    }),
  );
}

function showError(output, message) {
  const error = document.createElement("p");
  error.className = "lab-error";
  error.textContent = message;
  output.replaceChildren(error);
}

function renderCurrent(form, output, scenarios, labels) {
  const row = scenarios[scenarioKey(readState(form))];
  if (!row) {
    showError(output, form.dataset.missingError);
    return;
  }
  renderScenario(output, row, labels);
}

async function initLab() {
  const form = document.querySelector("[data-apr-lab]");
  if (!form) return;

  const output = form.querySelector("[data-lab-output]");
  try {
    const response = await fetch("/data/demo-scenarios.json");
    if (!response.ok) throw new Error("APR demo scenario fixture unavailable");
    const scenarios = validatePayload(await response.json());
    const labels = outputLabels(form);
    const update = () => renderCurrent(form, output, scenarios, labels);
    form.addEventListener("change", update);
    update();
  } catch {
    showError(output, form.dataset.loadError);
  } finally {
    output.removeAttribute("aria-busy");
  }
}

initLab();
