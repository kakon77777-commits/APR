from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .action_gate import ActionDecisionKind, ActionSpec
from .action_runtime import ActionReadinessRuntime
from .event_ledger import NativeEvent
from .execution_ledger import ExecutionLedger, ExecutionReceipt
from .outcome import (
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    OutcomeDecision,
    OutcomeDecisionKind,
)
from .task_runtime import TaskAwareIngestReport, TaskAwarePerceptionRuntime


@dataclass(frozen=True)
class OutcomeExecutionResult:
    executed: bool
    execution_id: Optional[str]
    readiness_kind: str
    result: Any = None


class ActionOutcomeRuntime:
    """
    Closed-loop action runtime:
      readiness -> execute -> request outcome verification -> verify -> recovery.

    Expected postconditions are declarations only. They are never written into
    WorldState as if they were observed.
    """

    def __init__(
        self,
        readiness: ActionReadinessRuntime,
        verifier: ActionOutcomeVerifier,
        execution_ledger: ExecutionLedger,
        *,
        perception_runtime: Optional[TaskAwarePerceptionRuntime] = None,
    ) -> None:
        self.readiness = readiness
        self.verifier = verifier
        self.execution_ledger = execution_ledger
        self.perception_runtime = perception_runtime
        self.outcomes: Dict[str, ActionOutcomeSpec] = {}

    def register_outcome(self, spec: ActionOutcomeSpec) -> None:
        self.outcomes[spec.action_id] = spec

    def _spec(self, action_id: str) -> ActionOutcomeSpec:
        if action_id not in self.outcomes:
            raise KeyError(f"No ActionOutcomeSpec registered for {action_id!r}.")
        return self.outcomes[action_id]

    def _capture_pre_state(self, spec: ActionOutcomeSpec) -> Dict[str, Any]:
        return {
            req.fact_key: self.verifier.world.get(req.fact_key).value for req in spec.postconditions
        }

    def execute(
        self,
        action: str | ActionSpec,
        func: Callable[[], Any],
        *,
        now: Optional[float] = None,
        retry_count: int = 0,
        parent_execution_id: Optional[str] = None,
        auto_request_verification: bool = True,
    ) -> OutcomeExecutionResult:
        action_spec = self.readiness.actions[action] if isinstance(action, str) else action
        outcome_spec = self._spec(action_spec.id)
        now = time.time() if now is None else float(now)

        decision = self.readiness.decision(action_spec, now=now)
        if decision.kind != ActionDecisionKind.ALLOW:
            if decision.kind == ActionDecisionKind.VERIFY and auto_request_verification:
                self.readiness.request_verification(action_spec, now=now)
            return OutcomeExecutionResult(
                executed=False,
                execution_id=None,
                readiness_kind=decision.kind.value,
            )

        pre_state = self._capture_pre_state(outcome_spec)
        started_at = now
        result = func()
        executed_at = time.time()

        receipt = ExecutionReceipt(
            action_id=action_spec.id,
            action_name=action_spec.name,
            started_at=started_at,
            executed_at=executed_at,
            readiness=decision.kind.value,
            result_repr=repr(result),
            retry_count=retry_count,
            parent_execution_id=parent_execution_id,
            status="executed",
            pre_state=pre_state,
        )
        self.execution_ledger.upsert(receipt)

        if auto_request_verification:
            self.request_outcome_verification(receipt.id)

        return OutcomeExecutionResult(
            executed=True,
            execution_id=receipt.id,
            readiness_kind=decision.kind.value,
            result=result,
        )

    def verification_events(
        self,
        execution_id: str,
        *,
        now: Optional[float] = None,
    ) -> List[NativeEvent]:
        receipt = self.execution_ledger.get(execution_id)
        if receipt is None:
            raise KeyError(execution_id)
        spec = self._spec(receipt.action_id)
        now = time.time() if now is None else float(now)

        return [
            NativeEvent(
                kind="apr.action.outcome.verify",
                source="action_outcome_runtime",
                target=req.fact_key,
                significance=min(
                    1.0,
                    0.45 + 0.45 * self.readiness.actions[receipt.action_id].risk,
                ),
                timestamp=now,
                payload={
                    "execution_id": receipt.id,
                    "action_id": receipt.action_id,
                    "fact_key": req.fact_key,
                    "expected_values": req.expected_values,
                    "forbidden_values": req.forbidden_values,
                    "executed_at": receipt.executed_at,
                    "affected_facts": {req.fact_key: 1.0},
                    "apr_explicit_need_urgency": min(
                        1.0,
                        0.55 + 0.40 * self.readiness.actions[receipt.action_id].risk,
                    ),
                },
            )
            for req in spec.postconditions
        ]

    def request_outcome_verification(
        self,
        execution_id: str,
        *,
        now: Optional[float] = None,
    ) -> TaskAwareIngestReport:
        if self.perception_runtime is None:
            return TaskAwareIngestReport()
        events = self.verification_events(execution_id, now=now)
        return self.perception_runtime.submit_native(
            events,
            now=now,
            persist=True,
        )

    def _link_post_action_evidence(self, receipt: ExecutionReceipt) -> None:
        spec = self._spec(receipt.action_id)
        for req in spec.postconditions:
            fact = self.verifier.world.get(req.fact_key)
            for evidence_id in fact.evidence_ids:
                ev = self.verifier.evidence_store.get(evidence_id)
                if ev is not None and ev.timestamp >= receipt.executed_at:
                    self.execution_ledger.link_evidence(
                        receipt.id,
                        evidence_id,
                        role="postcondition",
                    )

    def verify(
        self,
        execution_id: str,
        *,
        now: Optional[float] = None,
        auto_request_more_evidence: bool = True,
    ) -> OutcomeDecision:
        receipt = self.execution_ledger.get(execution_id)
        if receipt is None:
            raise KeyError(execution_id)

        spec = self._spec(receipt.action_id)
        decision = self.verifier.decide(
            spec,
            execution_id=receipt.id,
            executed_at=receipt.executed_at,
            pre_state=receipt.pre_state,
            retry_count=receipt.retry_count,
            now=now,
        )
        self._link_post_action_evidence(receipt)

        receipt.outcome = decision.kind.value
        if decision.kind == OutcomeDecisionKind.SUCCESS:
            receipt.status = "completed"
            receipt.completed_at = time.time()
        elif decision.kind == OutcomeDecisionKind.VERIFY:
            receipt.status = "verifying"
        elif decision.kind == OutcomeDecisionKind.RETRY:
            receipt.status = "retry_required"
        elif decision.kind == OutcomeDecisionKind.REPLAN:
            receipt.status = "replan_required"
        elif decision.kind == OutcomeDecisionKind.ROLLBACK:
            receipt.status = "rollback_required"
        else:
            receipt.status = "failed"
        self.execution_ledger.upsert(receipt)

        if (
            decision.kind == OutcomeDecisionKind.VERIFY
            and auto_request_more_evidence
            and self.perception_runtime is not None
        ):
            self.request_outcome_verification(receipt.id, now=now)

        return decision
