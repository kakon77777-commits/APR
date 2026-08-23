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
const PAYLOAD_FIELDS = ["schema", "runtime_version", "controls", "scenarios"];
const VALUE_LABEL_DOMAINS = {
  disposition: [
    "no_observation",
    "monitor",
    "skim",
    "search",
    "track",
    "inspect",
    "deep",
    "revisit",
    "epistemic_action",
  ],
  reason_key: [
    "fresh_fact_sufficient",
    "contradiction_revisit",
    "stale_fact_refresh",
    "fact_unknown_or_uncertain",
    "risk_reverification",
    "no_direct_modality",
  ],
  effective_fact_status: ["known", "unknown", "uncertain", "stale", "contradicted"],
  selected_channel: ["text", "vision", "video", "audio", "structured", "sensor", "none"],
  affordable: ["true", "false"],
  action_readiness: ["allow", "verify", "block"],
};

export function scenarioKey(state) {
  return CONTROL_ORDER.map((name) => state[name]).join(":");
}

function valueCode(value) {
  if (value === null) return "none";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return value;
  throw new Error("Invalid APR display value");
}

export function renderScenario(output, row, labels, valueLabels) {
  const documentRef = output.ownerDocument ?? globalThis.document;
  const list = documentRef.createElement("dl");
  for (const field of OUTPUT_FIELDS) {
    const term = documentRef.createElement("dt");
    term.textContent = labels[field];
    const detail = documentRef.createElement("dd");
    if (Object.hasOwn(VALUE_LABEL_DOMAINS, field)) {
      const code = valueCode(row[field]);
      const localized = valueLabels[field]?.[code];
      if (typeof localized !== "string" || localized.length === 0) {
        throw new Error(`Missing APR value label for ${field}:${code}`);
      }
      detail.textContent = localized;
    } else {
      detail.textContent = String(row[field]);
    }
    list.append(term, detail);
  }
  output.replaceChildren(list);
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasExactKeys(value, expected) {
  return (
    isRecord(value) &&
    Object.keys(value).length === expected.length &&
    expected.every((key) => Object.hasOwn(value, key))
  );
}

function parseValueLabels(form) {
  const parsed = JSON.parse(form.dataset.valueLabels);
  const fields = Object.keys(VALUE_LABEL_DOMAINS);
  if (!hasExactKeys(parsed, fields)) {
    throw new Error("Invalid APR locale value map");
  }
  for (const [field, domain] of Object.entries(VALUE_LABEL_DOMAINS)) {
    const labels = parsed[field];
    if (
      !hasExactKeys(labels, domain) ||
      !Object.values(labels).every((label) => typeof label === "string" && label.length > 0)
    ) {
      throw new Error(`Invalid APR locale value domain: ${field}`);
    }
  }
  return parsed;
}

function validatePayload(payload, valueLabels) {
  if (
    !hasExactKeys(payload, PAYLOAD_FIELDS) ||
    payload.schema !== "apr-demo-scenarios/v1" ||
    payload.runtime_version !== "0.10.0" ||
    !Array.isArray(payload.controls) ||
    payload.controls.length !== CONTROL_ORDER.length ||
    !payload.controls.every((name, index) => name === CONTROL_ORDER[index]) ||
    !isRecord(payload.scenarios)
  ) {
    throw new Error("Invalid APR demo scenario payload");
  }

  for (const [key, row] of Object.entries(payload.scenarios)) {
    if (
      !hasExactKeys(row, ROW_FIELDS) ||
      row.scenario_key !== key
    ) {
      throw new Error("Invalid APR demo scenario row");
    }
    for (const field of Object.keys(VALUE_LABEL_DOMAINS)) {
      const code = valueCode(row[field]);
      if (!Object.hasOwn(valueLabels[field], code)) {
        throw new Error(`Untranslated APR demo scenario value: ${field}:${code}`);
      }
    }
  }
  return payload.scenarios;
}

function readState(form, FormDataClass) {
  const formData = new FormDataClass(form);
  return Object.fromEntries(CONTROL_ORDER.map((name) => [name, formData.get(name)]));
}

function outputLabels(form) {
  const labels = Object.fromEntries(
    OUTPUT_FIELDS.map((field) => {
      const dataName = `label${field
        .split("_")
        .map((part) => part[0].toUpperCase() + part.slice(1))
        .join("")}`;
      return [field, form.dataset[dataName]];
    }),
  );
  if (!Object.values(labels).every((label) => typeof label === "string" && label.length > 0)) {
    throw new Error("Invalid APR output labels");
  }
  return labels;
}

function showError(output, message) {
  const documentRef = output.ownerDocument ?? globalThis.document;
  const error = documentRef.createElement("p");
  error.className = "lab-error";
  error.textContent = message;
  output.replaceChildren(error);
}

function renderCurrent(form, output, scenarios, labels, valueLabels, FormDataClass) {
  const row = scenarios[scenarioKey(readState(form, FormDataClass))];
  if (!row) {
    showError(output, form.dataset.missingError);
    return;
  }
  renderScenario(output, row, labels, valueLabels);
}

export async function initLab({
  document: documentRef = globalThis.document,
  fetch: fetchFixture = globalThis.fetch,
  FormData: FormDataClass = globalThis.FormData,
} = {}) {
  const form = documentRef?.querySelector("[data-apr-lab]");
  if (!form) return;

  const output = form.querySelector("[data-lab-output]");
  try {
    const labels = outputLabels(form);
    const valueLabels = parseValueLabels(form);
    const response = await fetchFixture("/data/demo-scenarios.json");
    if (!response.ok) throw new Error("APR demo scenario fixture unavailable");
    const scenarios = validatePayload(await response.json(), valueLabels);
    const update = () =>
      renderCurrent(form, output, scenarios, labels, valueLabels, FormDataClass);
    form.addEventListener("change", update);
    update();
  } catch {
    showError(output, form.dataset.loadError);
  } finally {
    output.removeAttribute("aria-busy");
  }
}

if (typeof document !== "undefined") {
  document.documentElement.dataset.site = "apr";
  void initLab();
}
