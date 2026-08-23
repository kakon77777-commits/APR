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
  disposition: "inspect",
  reason_key: "unresolved_goal",
  effective_fact_status: "unknown",
  selected_channel: "semantic",
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
  disposition: "block",
  reason_key: "high_risk_unresolved",
  effective_fact_status: "unknown",
  selected_channel: "semantic",
  expected_gain: 0.75,
  estimated_cost: 0.2,
  budget_before: 1,
  projected_budget_after: 0.8,
  affordable: true,
  action_readiness: "blocked",
  facts_to_verify: ["goal.fact"],
  blocking_facts: ["goal.fact"],
};

function validPayload(scenarios = { [DEFAULT_KEY]: DEFAULT_ROW, [CHANGED_KEY]: CHANGED_ROW }) {
  return {
    schema: "apr-demo-scenarios/v1",
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

function createHarness({ locale = "en", payload = validPayload() } = {}) {
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
      labelDisposition: "Disposition",
      labelReasonKey: "Reason",
      labelEffectiveFactStatus: "Effective fact status",
      labelSelectedChannel: "Selected channel",
      labelBudgetBefore: "Budget before",
      labelProjectedBudgetAfter: "Projected budget after",
      labelAffordable: "Affordable",
      labelActionReadiness: "Action readiness",
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
    "inspect",
    "unresolved_goal",
    "unknown",
    "semantic",
    "1",
    "0.8",
    "true",
    "verify",
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
    "block",
    "high_risk_unresolved",
    "unknown",
    "semantic",
    "1",
    "0.8",
    "true",
    "blocked",
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
