import assert from "node:assert/strict";
import test from "node:test";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const importDocument = {
  documentElement: { dataset: {} },
  querySelector() {
    return null;
  },
};
globalThis.document = importDocument;
const app = await import(pathToFileURL(resolve("site/src/assets/app.js")).href);
delete globalThis.document;

const CONTROL_ORDER = ["freshness", "uncertainty", "risk", "conflict", "budget", "goal"];
const DEFAULT_STATE = {
  freshness: "fresh",
  uncertainty: "low",
  risk: "low",
  conflict: "absent",
  budget: "available",
  goal: "unresolved",
};
const DEFAULT_KEY = "fresh:low:low:absent:available:unresolved";
const CHANGED_KEY = "fresh:low:high:absent:available:unresolved";
const DEFAULT_ROW = {
  scenario_key: DEFAULT_KEY,
  disposition: "search",
  reason_key: "fact_unknown_or_uncertain",
  effective_fact_status: "unknown",
  selected_channel: "structured",
  expected_gain: 0.75,
  estimated_cost: 0.2,
  budget_before: 1,
  projected_budget_after: 0.8,
  affordable: true,
  action_readiness: "verify",
  facts_to_verify: ["goal.fact"],
  blocking_facts: [],
};
const CHANGED_ROW = {
  scenario_key: CHANGED_KEY,
  disposition: "revisit",
  reason_key: "contradiction_revisit",
  effective_fact_status: "contradicted",
  selected_channel: "structured",
  expected_gain: 0.75,
  estimated_cost: 0.2,
  budget_before: 1,
  projected_budget_after: 0.8,
  affordable: true,
  action_readiness: "block",
  facts_to_verify: ["goal.fact"],
  blocking_facts: ["goal.fact"],
};

const VALUE_LABELS_EN = {
  disposition: {
    no_observation: "No observation",
    monitor: "Monitor",
    skim: "Skim",
    search: "Search",
    track: "Track",
    inspect: "Inspect",
    deep: "Deep read",
    revisit: "Revisit",
    epistemic_action: "Epistemic action",
  },
  reason_key: {
    fresh_fact_sufficient: "Fresh fact is sufficient",
    contradiction_revisit: "Contradiction requires re-observation",
    stale_fact_refresh: "Stale fact requires refresh",
    fact_unknown_or_uncertain: "Fact is unknown or uncertain",
    risk_reverification: "Risk requires re-verification",
    no_direct_modality: "No direct observation channel",
  },
  effective_fact_status: {
    known: "Known",
    unknown: "Unknown",
    uncertain: "Uncertain",
    stale: "Stale",
    contradicted: "Contradicted",
  },
  selected_channel: {
    text: "Text",
    vision: "Vision",
    video: "Video",
    audio: "Audio",
    structured: "Structured data",
    sensor: "Sensor",
    none: "No channel selected",
  },
  affordable: { true: "Yes", false: "No" },
  action_readiness: {
    allow: "Allow",
    verify: "Verify first",
    block: "Block",
  },
};

const VALUE_LABELS_ZH = {
  disposition: {
    no_observation: "不觀察",
    monitor: "監看",
    skim: "略讀",
    search: "搜尋",
    track: "追蹤",
    inspect: "檢視",
    deep: "深度閱讀",
    revisit: "重新觀察",
    epistemic_action: "認知行動",
  },
  reason_key: {
    fresh_fact_sufficient: "新鮮事實已足夠",
    contradiction_revisit: "矛盾需要重新觀察",
    stale_fact_refresh: "過期事實需要更新",
    fact_unknown_or_uncertain: "事實未知或不確定",
    risk_reverification: "風險要求再次驗證",
    no_direct_modality: "沒有直接觀察通道",
  },
  effective_fact_status: {
    known: "已知",
    unknown: "未知",
    uncertain: "不確定",
    stale: "過期",
    contradicted: "相互矛盾",
  },
  selected_channel: {
    text: "文字",
    vision: "視覺",
    video: "影片",
    audio: "音訊",
    structured: "結構化資料",
    sensor: "感測器",
    none: "未選擇通道",
  },
  affordable: { true: "可負擔", false: "不可負擔" },
  action_readiness: {
    allow: "允許",
    verify: "先驗證",
    block: "阻擋",
  },
};

const OUTPUT_LABELS_EN = {
  disposition: "Observation disposition",
  reason_key: "Reason",
  effective_fact_status: "Effective fact status",
  selected_channel: "Selected channel",
  budget_before: "Budget before",
  projected_budget_after: "Projected budget after",
  affordable: "Affordable",
  action_readiness: "Action readiness",
};

const OUTPUT_LABELS_ZH = {
  disposition: "觀察處置",
  reason_key: "理由",
  effective_fact_status: "有效事實狀態",
  selected_channel: "所選通道",
  budget_before: "預算前值",
  projected_budget_after: "預估預算後值",
  affordable: "可負擔性",
  action_readiness: "行動就緒狀態",
};

function validPayload(scenarios = { [DEFAULT_KEY]: DEFAULT_ROW, [CHANGED_KEY]: CHANGED_ROW }) {
  return {
    schema: "apr-demo-scenarios/v1",
    runtime_version: "0.10.0",
    controls: CONTROL_ORDER,
    scenarios,
  };
}

function createElement(tagName, ownerDocument) {
  return {
    tagName,
    ownerDocument,
    className: "",
    textContent: "",
    children: [],
    attributes: new Map(),
    append(...children) {
      this.children.push(...children);
    },
    replaceChildren(...children) {
      this.children = children;
    },
    removeAttribute(name) {
      this.attributes.delete(name);
    },
  };
}

function createHarness({ locale = "en", payload = validPayload(), valueLabels } = {}) {
  const listeners = {};
  const calls = [];
  const documentRef = {
    documentElement: { dataset: {} },
    createElement(tagName) {
      return createElement(tagName, documentRef);
    },
  };
  const output = createElement("output", documentRef);
  output.attributes.set("aria-busy", "true");
  const fieldLabels = locale === "zh-TW" ? OUTPUT_LABELS_ZH : OUTPUT_LABELS_EN;
  const selectedValueLabels = valueLabels ?? (locale === "zh-TW" ? VALUE_LABELS_ZH : VALUE_LABELS_EN);
  const form = {
    values: { ...DEFAULT_STATE },
    dataset: {
      locale,
      loadError:
        locale === "zh-TW"
          ? "本機固定案例無法通過驗證，因此教育投影目前不可用。"
          : "The educational projection is unavailable because its local fixture could not be validated.",
      missingError:
        locale === "zh-TW"
          ? "沒有符合此控制狀態的有界固定案例。"
          : "No bounded fixture matches this control state.",
      labelDisposition: fieldLabels.disposition,
      labelReasonKey: fieldLabels.reason_key,
      labelEffectiveFactStatus: fieldLabels.effective_fact_status,
      labelSelectedChannel: fieldLabels.selected_channel,
      labelBudgetBefore: fieldLabels.budget_before,
      labelProjectedBudgetAfter: fieldLabels.projected_budget_after,
      labelAffordable: fieldLabels.affordable,
      labelActionReadiness: fieldLabels.action_readiness,
      valueLabels:
        typeof selectedValueLabels === "string"
          ? selectedValueLabels
          : JSON.stringify(selectedValueLabels),
    },
    querySelector(selector) {
      assert.equal(selector, "[data-lab-output]");
      return output;
    },
    addEventListener(name, listener) {
      listeners[name] = listener;
    },
  };
  documentRef.querySelector = (selector) => {
    assert.equal(selector, "[data-apr-lab]");
    return form;
  };
  class FakeFormData {
    constructor(target) {
      this.target = target;
    }

    get(name) {
      return this.target.values[name];
    }
  }
  const fetchFixture = async (url) => {
    calls.push(url);
    return {
      ok: true,
      async json() {
        return payload;
      },
    };
  };
  return { calls, documentRef, FakeFormData, fetchFixture, form, listeners, output };
}

function renderedDetails(output) {
  assert.equal(output.children.length, 1);
  const [list] = output.children;
  assert.equal(list.tagName, "dl");
  return list.children.filter((child) => child.tagName === "dd").map((child) => child.textContent);
}

test("scenarioKey preserves the exact public control order", () => {
  const reversedState = Object.fromEntries(
    Object.entries(DEFAULT_STATE).reverse(),
  );
  assert.equal(app.scenarioKey(reversedState), DEFAULT_KEY);
});

test("initialization fetches the same-origin fixture exactly once", async () => {
  const harness = createHarness();
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  assert.deepEqual(harness.calls, ["/data/demo-scenarios.json"]);
});

test("initialization renders the default control state", async () => {
  const harness = createHarness();
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  assert.deepEqual(renderedDetails(harness.output), [
    "Search",
    "Fact is unknown or uncertain",
    "Unknown",
    "Structured data",
    "1",
    "0.8",
    "Yes",
    "Verify first",
  ]);
  assert.equal(harness.output.attributes.has("aria-busy"), false);
});

test("a changed control renders the matching scenario without refetching", async () => {
  const harness = createHarness();
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  harness.form.values.risk = "high";
  harness.listeners.change();
  assert.deepEqual(renderedDetails(harness.output), [
    "Revisit",
    "Contradiction requires re-observation",
    "Contradicted",
    "Structured data",
    "1",
    "0.8",
    "Yes",
    "Block",
  ]);
  assert.equal(harness.calls.length, 1);
});

test("an invalid payload renders the localized load error", async () => {
  const harness = createHarness({ locale: "zh-TW", payload: { schema: "invalid" } });
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  assert.equal(harness.output.children[0].className, "lab-error");
  assert.equal(
    harness.output.children[0].textContent,
    "本機固定案例無法通過驗證，因此教育投影目前不可用。",
  );
});

test("an extra payload field fails exact schema validation visibly", async () => {
  const harness = createHarness({
    locale: "zh-TW",
    payload: { ...validPayload(), unexpected: true },
  });
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  assert.equal(harness.output.children[0].className, "lab-error");
  assert.equal(
    harness.output.children[0].textContent,
    "本機固定案例無法通過驗證，因此教育投影目前不可用。",
  );
});

test("a malformed locale value map renders the localized load error", async () => {
  const harness = createHarness({ locale: "zh-TW", valueLabels: "not-json" });
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  assert.equal(harness.output.children[0].className, "lab-error");
  assert.equal(
    harness.output.children[0].textContent,
    "本機固定案例無法通過驗證，因此教育投影目前不可用。",
  );
});

test("Chinese rendering localizes every distinct real matrix value and null", () => {
  const harness = createHarness({ locale: "zh-TW" });
  const cases = {
    disposition: [
      ["inspect", "檢視"],
      ["no_observation", "不觀察"],
      ["revisit", "重新觀察"],
      ["search", "搜尋"],
    ],
    reason_key: [
      ["contradiction_revisit", "矛盾需要重新觀察"],
      ["fact_unknown_or_uncertain", "事實未知或不確定"],
      ["fresh_fact_sufficient", "新鮮事實已足夠"],
      ["risk_reverification", "風險要求再次驗證"],
      ["stale_fact_refresh", "過期事實需要更新"],
    ],
    effective_fact_status: [
      ["contradicted", "相互矛盾"],
      ["known", "已知"],
      ["stale", "過期"],
      ["uncertain", "不確定"],
      ["unknown", "未知"],
    ],
    selected_channel: [
      ["structured", "結構化資料"],
      [null, "未選擇通道"],
    ],
    affordable: [
      [true, "可負擔"],
      [false, "不可負擔"],
    ],
    action_readiness: [
      ["allow", "允許"],
      ["block", "阻擋"],
      ["verify", "先驗證"],
    ],
  };
  const outputIndexes = Object.fromEntries(
    [
      "disposition",
      "reason_key",
      "effective_fact_status",
      "selected_channel",
      "budget_before",
      "projected_budget_after",
      "affordable",
      "action_readiness",
    ].map((field, index) => [field, index]),
  );

  for (const [field, fieldCases] of Object.entries(cases)) {
    for (const [machineValue, expectedLabel] of fieldCases) {
      const row = { ...DEFAULT_ROW, [field]: machineValue };
      app.renderScenario(harness.output, row, OUTPUT_LABELS_ZH, VALUE_LABELS_ZH);
      assert.equal(
        renderedDetails(harness.output)[outputIndexes[field]],
        expectedLabel,
        `${field}:${String(machineValue)}`,
      );
    }
  }
});

test("a missing scenario key renders the localized lookup error", async () => {
  const harness = createHarness({
    locale: "zh-TW",
    payload: validPayload({ [DEFAULT_KEY]: DEFAULT_ROW }),
  });
  await app.initLab({
    document: harness.documentRef,
    fetch: harness.fetchFixture,
    FormData: harness.FakeFormData,
  });
  harness.form.values.risk = "high";
  harness.listeners.change();
  assert.equal(harness.output.children[0].className, "lab-error");
  assert.equal(harness.output.children[0].textContent, "沒有符合此控制狀態的有界固定案例。");
});
