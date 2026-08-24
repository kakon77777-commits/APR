from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Literal

from apr_runtime.action_gate import (
    ActionReadinessGate,
    ActionSpec,
    FactRequirement,
)
from apr_runtime.adapters import ObservationSpec, SimulatorAdapter
from apr_runtime.evidence import EvidenceStore
from apr_runtime.models import (
    Budget,
    Evidence,
    Goal,
    Modality,
    PerceptualAction,
    ReadingMode,
)
from apr_runtime.policy import ChannelProfile, PolicyController
from apr_runtime.runtime import APRRuntime
from apr_runtime.world_state import WorldState

_REASON_KEYS = {
    "Existing world-state fact is fresh and sufficiently confident.": "fresh_fact_sufficient",
    "Fact is contradicted; targeted re-observation is required.": "contradiction_revisit",
    "Fact is stale; refresh the current belief.": "stale_fact_refresh",
    "Required fact is unknown/uncertain.": "fact_unknown_or_uncertain",
    "Risk threshold requests re-verification before action.": "risk_reverification",
    "No direct modality is available; change observation conditions.": "no_direct_modality",
}

_CONTROL_VALUES = (
    ("fresh", "stale"),
    ("low", "high"),
    ("low", "high"),
    ("absent", "present"),
    ("available", "exhausted"),
    ("unresolved", "satisfied"),
)


@dataclass(frozen=True)
class DemoScenarioInput:
    freshness: Literal["fresh", "stale"]
    uncertainty: Literal["low", "high"]
    risk: Literal["low", "high"]
    conflict: Literal["absent", "present"]
    budget: Literal["available", "exhausted"]
    goal: Literal["unresolved", "satisfied"]

    def key(self) -> str:
        return ":".join(
            (
                self.freshness,
                self.uncertainty,
                self.risk,
                self.conflict,
                self.budget,
                self.goal,
            )
        )


def reason_key(action: PerceptualAction) -> str:
    try:
        return _REASON_KEYS[action.reason]
    except KeyError as exc:
        raise ValueError(f"Untranslated APR decision reason: {action.reason}") from exc


def _build_runtime(scenario: DemoScenarioInput) -> APRRuntime:
    store = EvidenceStore()
    world = WorldState(store)
    structured = SimulatorAdapter(
        modality=Modality.STRUCTURED,
        source="demo_sensor",
        world={"demo.ready": ObservationSpec(True, confidence=0.95)},
        reliability=0.99,
        base_cost=1.0,
    )
    vision = SimulatorAdapter(
        modality=Modality.VISION,
        source="demo_vision",
        world={"demo.ready": ObservationSpec(True, confidence=0.95)},
        reliability=0.95,
        base_cost=5.0,
    )
    profiles = {
        Modality.STRUCTURED: ChannelProfile(
            Modality.STRUCTURED,
            reliability=0.99,
            cost=1.0,
            directness=1.0,
        ),
        Modality.VISION: ChannelProfile(
            Modality.VISION,
            reliability=0.95,
            cost=5.0,
            directness=0.65,
        ),
    }
    budget = 10.0 if scenario.budget == "available" else 0.0
    return APRRuntime(
        world=world,
        evidence_store=store,
        policy=PolicyController(profiles),
        budget=Budget(units=budget),
        adapters={Modality.STRUCTURED: structured, Modality.VISION: vision},
    )


def _seed_world(runtime: APRRuntime, scenario: DemoScenarioInput) -> None:
    confidence = 0.95 if scenario.uncertainty == "low" else 0.40

    if scenario.conflict == "present":
        runtime.world.revise(
            Evidence(
                claim_key="demo.ready",
                observed_value=True,
                modality=Modality.STRUCTURED,
                source="demo_sensor",
                confidence=0.95,
                cost=0.0,
            )
        )
        runtime.world.revise(
            Evidence(
                claim_key="demo.ready",
                observed_value=False,
                modality=Modality.VISION,
                source="demo_vision",
                confidence=0.95,
                cost=0.0,
            )
        )
    elif scenario.goal == "satisfied":
        runtime.world.revise(
            Evidence(
                claim_key="demo.ready",
                observed_value=True,
                modality=Modality.STRUCTURED,
                source="demo_sensor",
                confidence=confidence,
                cost=0.0,
            )
        )

    fact = runtime.world.get("demo.ready")
    if scenario.freshness == "stale" and fact.value is not None:
        fact.ttl = 0.0
        fact.last_verified = 1.0


def evaluate_scenario(scenario: DemoScenarioInput) -> dict[str, object]:
    runtime = _build_runtime(scenario)
    _seed_world(runtime, scenario)
    risk = 0.90 if scenario.risk == "high" else 0.25
    action = runtime.decide(Goal("demo.ready", risk=risk, min_confidence=0.80))
    affordable = runtime.budget_controller.affordable(action)
    gate_decision = ActionReadinessGate(runtime.world, runtime.evidence_store).evaluate(
        ActionSpec(
            id="demo.action",
            name="Demo action",
            risk=risk,
            requirements=(
                FactRequirement(
                    "demo.ready",
                    min_confidence=0.80,
                    allowed_values=(True,),
                ),
            ),
        )
    )

    return {
        "scenario_key": scenario.key(),
        "disposition": action.mode.value,
        "reason_key": reason_key(action),
        "effective_fact_status": runtime.world.get("demo.ready").status.value,
        "selected_channel": action.modality.value if action.modality else None,
        "expected_gain": round(action.expected_gain, 3),
        "estimated_cost": round(action.estimated_cost, 3),
        "budget_before": round(runtime.budget.remaining, 3),
        "projected_budget_after": round(
            runtime.budget.remaining - action.estimated_cost
            if affordable and action.mode != ReadingMode.NO_OBSERVATION
            else runtime.budget.remaining,
            3,
        ),
        "affordable": affordable,
        "action_readiness": gate_decision.kind.value,
        "facts_to_verify": list(gate_decision.facts_to_verify),
        "blocking_facts": list(gate_decision.blocking_facts),
    }


def export_scenarios() -> dict[str, dict[str, object]]:
    scenarios: dict[str, dict[str, object]] = {}
    for values in product(*_CONTROL_VALUES):
        scenario = DemoScenarioInput(*values)
        scenarios[scenario.key()] = evaluate_scenario(scenario)
    return scenarios
