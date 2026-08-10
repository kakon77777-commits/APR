from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .action_gate import (
    ActionDecision,
    ActionDecisionKind,
    ActionReadinessGate,
    ActionSpec,
)
from .event_ledger import NativeEvent
from .need_graph import PerceptualNeed, PerceptualNeedGraph
from .task_runtime import TaskAwareIngestReport, TaskAwarePerceptionRuntime


@dataclass(frozen=True)
class ActionExecutionResult:
    decision: ActionDecision
    executed: bool
    result: Any = None


class ActionReadinessRuntime:
    """
    Bridge Planner/Action Runtime to APR perception governance.

    Registration makes action preconditions visible to the Perceptual Need
    Graph. Evaluation gates execution. VERIFY creates perception work; BLOCK
    never executes the action.
    """

    def __init__(
        self,
        gate: ActionReadinessGate,
        *,
        needs: Optional[PerceptualNeedGraph] = None,
        perception_runtime: Optional[TaskAwarePerceptionRuntime] = None,
    ) -> None:
        self.gate = gate
        self.needs = needs
        self.perception_runtime = perception_runtime
        self.actions: Dict[str, ActionSpec] = {}

    @staticmethod
    def _need_id(action_id: str, fact_key: str) -> str:
        return f"action::{action_id}::{fact_key}"

    def register(self, action: ActionSpec) -> None:
        self.actions[action.id] = action
        if self.needs is None:
            return

        for req in action.requirements:
            need_id = self._need_id(action.id, req.fact_key)
            if need_id in self.needs.needs:
                continue
            self.needs.add_need(
                PerceptualNeed(
                    id=need_id,
                    fact_key=req.fact_key,
                    description=(
                        req.description or f"Evidence precondition for action {action.name}"
                    ),
                    min_confidence=self.gate._effective_min_confidence(action, req),
                    risk=action.risk,
                    weight=max(0.1, req.weight),
                    mandatory=True,
                    refresh_interval=req.max_age,
                )
            )

    def decision(
        self,
        action: str | ActionSpec,
        *,
        now: Optional[float] = None,
    ) -> ActionDecision:
        spec = self.actions[action] if isinstance(action, str) else action
        return self.gate.evaluate(spec, now=now)

    def verification_events(
        self,
        action: str | ActionSpec,
        decision: Optional[ActionDecision] = None,
        *,
        now: Optional[float] = None,
    ) -> List[NativeEvent]:
        spec = self.actions[action] if isinstance(action, str) else action
        now = time.time() if now is None else float(now)
        decision = decision or self.gate.evaluate(spec, now=now)

        if decision.kind != ActionDecisionKind.VERIFY:
            return []

        by_fact = {a.fact_key: a for a in decision.assessments}
        out: List[NativeEvent] = []

        for fact_key in decision.facts_to_verify:
            assessment = by_fact[fact_key]
            out.append(
                NativeEvent(
                    kind="apr.action.verify",
                    source="action_gate",
                    target=fact_key,
                    significance=max(
                        0.25,
                        min(1.0, assessment.urgency),
                    ),
                    timestamp=now,
                    payload={
                        "action_id": spec.id,
                        "action_name": spec.name,
                        "action_risk": spec.risk,
                        "fact_key": fact_key,
                        "precondition_state": assessment.state.value,
                        "required_confidence": assessment.required_confidence,
                        "current_confidence": assessment.confidence,
                        "max_age": assessment.max_age,
                        "affected_facts": {fact_key: 1.0},
                        "apr_explicit_need_urgency": assessment.urgency,
                        "reason": assessment.reason,
                    },
                )
            )
        return out

    def request_verification(
        self,
        action: str | ActionSpec,
        *,
        now: Optional[float] = None,
        persist: bool = True,
    ) -> TaskAwareIngestReport:
        if self.perception_runtime is None:
            return TaskAwareIngestReport()

        decision = self.decision(action, now=now)
        events = self.verification_events(
            action,
            decision,
            now=now,
        )
        if not events:
            return TaskAwareIngestReport()

        return self.perception_runtime.submit_native(
            events,
            now=now,
            persist=persist,
        )

    def execute(
        self,
        action: str | ActionSpec,
        func: Callable[[], Any],
        *,
        now: Optional[float] = None,
        auto_request_verification: bool = True,
    ) -> ActionExecutionResult:
        decision = self.decision(action, now=now)

        if decision.kind == ActionDecisionKind.ALLOW:
            return ActionExecutionResult(
                decision=decision,
                executed=True,
                result=func(),
            )

        if (
            decision.kind == ActionDecisionKind.VERIFY
            and auto_request_verification
            and self.perception_runtime is not None
        ):
            self.request_verification(action, now=now)

        return ActionExecutionResult(
            decision=decision,
            executed=False,
            result=None,
        )
