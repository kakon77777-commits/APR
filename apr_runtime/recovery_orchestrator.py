from __future__ import annotations

import inspect
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .action_gate import ActionDecisionKind, ActionSpec
from .action_runtime import ActionReadinessRuntime
from .execution_ledger import ExecutionLedger
from .outcome import (
    ActionOutcomeSpec,
    OutcomeDecision,
    OutcomeDecisionKind,
    PostconditionState,
)
from .outcome_runtime import ActionOutcomeRuntime


class ReversibilityClass(str, Enum):
    REVERSIBLE = "reversible"
    COMPENSATABLE = "compensatable"
    IRREVERSIBLE = "irreversible"


class RetryMode(str, Enum):
    NEVER = "never"
    IDEMPOTENT = "idempotent"
    DEDUPLICATED = "deduplicated"


class PartialSuccessPolicy(str, Enum):
    REPLAN = "replan"
    ACCEPT = "accept"
    COMPENSATE = "compensate"


class RecoveryRunStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_ACCEPTED = "partial_accepted"
    WAITING_FOR_EVIDENCE = "waiting_for_evidence"
    BLOCKED = "blocked"
    REPLAN_REQUIRED = "replan_required"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class ExecutionCancelled(RuntimeError):
    pass


class ExecutionDeadlineExceeded(RuntimeError):
    pass


@dataclass
class RecoveryContext:
    run_id: str
    action_id: str
    attempt: int
    deadline: Optional[float] = None
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True

    def checkpoint(self) -> None:
        if self.cancelled:
            raise ExecutionCancelled(f"Execution {self.run_id} was cancelled.")
        if self.deadline is not None and time.time() > self.deadline:
            raise ExecutionDeadlineExceeded(f"Execution {self.run_id} exceeded its deadline.")


@dataclass(frozen=True)
class RecoveryPolicy:
    reversibility: ReversibilityClass = ReversibilityClass.COMPENSATABLE
    retry_mode: RetryMode = RetryMode.NEVER
    max_attempts: int = 1
    max_recovery_steps: int = 8
    overall_timeout: Optional[float] = 30.0
    rollback_action_id: Optional[str] = None
    partial_success: PartialSuccessPolicy = PartialSuccessPolicy.REPLAN
    require_verified_rollback: bool = True
    description: str = ""


@dataclass
class RecoveryTraceStep:
    kind: str
    timestamp: float
    action_id: Optional[str] = None
    execution_id: Optional[str] = None
    decision: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryTrace:
    run_id: str
    root_action_id: str
    started_at: float
    completed_at: Optional[float] = None
    status: Optional[RecoveryRunStatus] = None
    root_execution_id: Optional[str] = None
    steps: List[RecoveryTraceStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add(
        self,
        kind: str,
        *,
        action_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        decision: Optional[str] = None,
        **detail: Any,
    ) -> None:
        self.steps.append(
            RecoveryTraceStep(
                kind=kind,
                timestamp=time.time(),
                action_id=action_id,
                execution_id=execution_id,
                decision=decision,
                detail=detail,
            )
        )

    def finish(self, status: RecoveryRunStatus) -> None:
        self.status = status
        self.completed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "root_action_id": self.root_action_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": None if self.status is None else self.status.value,
            "root_execution_id": self.root_execution_id,
            "metadata": self.metadata,
            "steps": [
                {
                    "kind": step.kind,
                    "timestamp": step.timestamp,
                    "action_id": step.action_id,
                    "execution_id": step.execution_id,
                    "decision": step.decision,
                    "detail": step.detail,
                }
                for step in self.steps
            ],
        }

    def export_json(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return path

    def export_markdown(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# APR Recovery Trace — {self.run_id}",
            "",
            f"- Root action: `{self.root_action_id}`",
            f"- Status: `{None if self.status is None else self.status.value}`",
            f"- Started: `{self.started_at}`",
            f"- Completed: `{self.completed_at}`",
            "",
            "## Steps",
            "",
        ]
        for index, step in enumerate(self.steps, 1):
            lines.extend(
                [
                    f"### {index}. {step.kind}",
                    "",
                    f"- action: `{step.action_id}`",
                    f"- execution: `{step.execution_id}`",
                    f"- decision: `{step.decision}`",
                    f"- timestamp: `{step.timestamp}`",
                    "",
                    "```json",
                    json.dumps(
                        step.detail,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    "```",
                    "",
                ]
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


@dataclass(frozen=True)
class RecoveryRunResult:
    status: RecoveryRunStatus
    trace: RecoveryTrace
    final_execution_id: Optional[str] = None
    rollback_execution_id: Optional[str] = None
    result: Any = None


class ClosedLoopRecoveryOrchestrator:
    """
    Execute action/retry/compensation through the same readiness and outcome
    verification layers.

    Important semantics:
    - rollback means an explicit compensating action, not time reversal;
    - automatic retry is allowed only when the action's RecoveryPolicy says so;
    - irreversible actions are never automatically retried unless the policy
      declares DEDUPLICATED and an idempotency key is supplied;
    - rollback actions themselves pass readiness and outcome verification.
    """

    def __init__(
        self,
        readiness: ActionReadinessRuntime,
        outcomes: ActionOutcomeRuntime,
        execution_ledger: ExecutionLedger,
    ) -> None:
        self.readiness = readiness
        self.outcomes = outcomes
        self.execution_ledger = execution_ledger
        self.handlers: Dict[str, Callable[..., Any]] = {}
        self.policies: Dict[str, RecoveryPolicy] = {}
        self.observers: Dict[str, Callable[[str, RecoveryContext], Any]] = {}

    def register(
        self,
        action: ActionSpec,
        outcome: ActionOutcomeSpec,
        handler: Callable[..., Any],
        *,
        recovery: Optional[RecoveryPolicy] = None,
        observer: Optional[Callable[[str, RecoveryContext], Any]] = None,
    ) -> None:
        if action.id not in self.readiness.actions:
            self.readiness.register(action)
        self.outcomes.register_outcome(outcome)
        self.handlers[action.id] = handler
        self.policies[action.id] = recovery or RecoveryPolicy()
        if observer is not None:
            self.observers[action.id] = observer

    @staticmethod
    def _call(func: Callable[..., Any], context: RecoveryContext) -> Any:
        try:
            signature = inspect.signature(func)
            accepts_arg = len(signature.parameters) > 0
        except (TypeError, ValueError):
            accepts_arg = False

        context.checkpoint()
        result = func(context) if accepts_arg else func()
        context.checkpoint()
        return result

    def _retry_allowed(
        self,
        policy: RecoveryPolicy,
        context: RecoveryContext,
        *,
        next_attempt: int,
    ) -> Tuple[bool, str]:
        if next_attempt > max(1, policy.max_attempts):
            return False, "Retry budget exhausted."

        if policy.retry_mode == RetryMode.NEVER:
            return False, "Recovery policy forbids automatic retry."

        if (
            policy.reversibility == ReversibilityClass.IRREVERSIBLE
            and policy.retry_mode != RetryMode.DEDUPLICATED
        ):
            return (
                False,
                "Irreversible action cannot be auto-retried without "
                "deduplication/idempotency protection.",
            )

        if policy.retry_mode == RetryMode.DEDUPLICATED:
            if not context.idempotency_key:
                return (
                    False,
                    "Deduplicated retry requires an idempotency key.",
                )

        return True, "Retry permitted by recovery policy."

    @staticmethod
    def _partial(outcome: OutcomeDecision) -> bool:
        states = {a.state for a in outcome.assessments}
        return PostconditionState.SATISFIED in states and any(
            state in states
            for state in (
                PostconditionState.FAILED,
                PostconditionState.CONTRADICTED,
                PostconditionState.NEEDS_VERIFICATION,
            )
        )

    def _execute_once(
        self,
        action_id: str,
        trace: RecoveryTrace,
        *,
        context: RecoveryContext,
        retry_count: int = 0,
        parent_execution_id: Optional[str] = None,
    ):
        if action_id not in self.handlers:
            raise KeyError(f"No handler registered for {action_id!r}.")

        readiness = self.readiness.decision(action_id)
        trace.add(
            "readiness",
            action_id=action_id,
            decision=readiness.kind.value,
            reason=readiness.reason,
            facts_to_verify=list(readiness.facts_to_verify),
            blocking_facts=list(readiness.blocking_facts),
        )

        if readiness.kind != ActionDecisionKind.ALLOW:
            if readiness.kind == ActionDecisionKind.VERIFY:
                self.readiness.request_verification(action_id)
            return None, readiness.kind.value, None

        handler = self.handlers[action_id]
        result = self.outcomes.execute(
            action_id,
            lambda: self._call(handler, context),
            retry_count=retry_count,
            parent_execution_id=parent_execution_id,
            auto_request_verification=False,
        )
        if not result.executed:
            return None, result.readiness_kind, None

        execution_id = result.execution_id
        if trace.root_execution_id is None:
            trace.root_execution_id = execution_id

        trace.add(
            "execute",
            action_id=action_id,
            execution_id=execution_id,
            decision="executed",
            attempt=context.attempt,
            retry_count=retry_count,
            idempotency_key=context.idempotency_key,
            result_repr=repr(result.result),
        )

        observer = self.observers.get(action_id)
        if observer is not None:
            context.checkpoint()
            observer(execution_id, context)
            context.checkpoint()
            trace.add(
                "observe_outcome",
                action_id=action_id,
                execution_id=execution_id,
                decision="observer_completed",
            )

        outcome = self.outcomes.verify(
            execution_id,
            auto_request_more_evidence=False,
        )
        trace.add(
            "verify_outcome",
            action_id=action_id,
            execution_id=execution_id,
            decision=outcome.kind.value,
            facts_to_verify=list(outcome.facts_to_verify),
            failed_facts=list(outcome.failed_facts),
            partial=self._partial(outcome),
        )
        return execution_id, outcome, result.result

    def _run_compensation(
        self,
        rollback_id: str,
        trace: RecoveryTrace,
        *,
        deadline: Optional[float],
        idempotency_key: Optional[str],
        metadata: Dict[str, Any],
        parent_execution_id: str,
    ):
        """
        Execute a compensating action through its own gate/outcome policy.
        A compensation may retry only if its own RecoveryPolicy allows it.
        We intentionally do not recursively compensate a failed compensation;
        such a failure escalates to ROLLBACK_FAILED / human or planner recovery.
        """
        if rollback_id not in self.handlers:
            return None, None, None, "missing_handler"

        policy = self.policies.get(
            rollback_id,
            RecoveryPolicy(
                reversibility=ReversibilityClass.REVERSIBLE,
                retry_mode=RetryMode.NEVER,
            ),
        )
        context = RecoveryContext(
            run_id=trace.run_id,
            action_id=rollback_id,
            attempt=1,
            deadline=deadline,
            idempotency_key=idempotency_key,
            metadata={
                **metadata,
                "compensates_execution_id": parent_execution_id,
            },
        )
        parent = parent_execution_id

        while context.attempt <= max(1, policy.max_attempts):
            execution_id, decision, result = self._execute_once(
                rollback_id,
                trace,
                context=context,
                retry_count=context.attempt - 1,
                parent_execution_id=parent,
            )

            if execution_id is None:
                return execution_id, decision, result, "gate_failed"

            if decision.kind == OutcomeDecisionKind.SUCCESS:
                return execution_id, decision, result, "success"

            if decision.kind == OutcomeDecisionKind.VERIFY:
                self.outcomes.request_outcome_verification(execution_id)
                return execution_id, decision, result, "waiting_for_evidence"

            if decision.kind == OutcomeDecisionKind.RETRY:
                next_attempt = context.attempt + 1
                allowed, reason = self._retry_allowed(
                    policy,
                    context,
                    next_attempt=next_attempt,
                )
                trace.add(
                    "rollback_retry_decision",
                    action_id=rollback_id,
                    execution_id=execution_id,
                    decision="allow" if allowed else "deny",
                    reason=reason,
                    next_attempt=next_attempt,
                )
                if not allowed:
                    return execution_id, decision, result, "retry_denied"

                parent = execution_id
                context.attempt = next_attempt
                continue

            return execution_id, decision, result, "failed"

        return None, None, None, "retry_exhausted"

    def run(
        self,
        action_id: str,
        *,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryRunResult:
        if action_id not in self.policies:
            raise KeyError(f"No recovery policy registered for {action_id!r}.")

        started = time.time()
        trace = RecoveryTrace(
            run_id=str(uuid.uuid4()),
            root_action_id=action_id,
            started_at=started,
            metadata=dict(metadata or {}),
        )
        policy = self.policies[action_id]
        deadline = (
            None if policy.overall_timeout is None else started + max(0.0, policy.overall_timeout)
        )

        context = RecoveryContext(
            run_id=trace.run_id,
            action_id=action_id,
            attempt=1,
            deadline=deadline,
            idempotency_key=idempotency_key,
            metadata=dict(metadata or {}),
        )

        recovery_steps = 0
        parent_execution_id = None
        last_result = None

        try:
            while recovery_steps < max(1, policy.max_recovery_steps):
                context.checkpoint()

                execution_id, decision, result = self._execute_once(
                    action_id,
                    trace,
                    context=context,
                    retry_count=context.attempt - 1,
                    parent_execution_id=parent_execution_id,
                )
                last_result = result

                if execution_id is None:
                    if decision == ActionDecisionKind.VERIFY.value:
                        trace.finish(RecoveryRunStatus.WAITING_FOR_EVIDENCE)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            result=last_result,
                        )
                    trace.finish(RecoveryRunStatus.BLOCKED)
                    return RecoveryRunResult(
                        trace.status,
                        trace,
                        result=last_result,
                    )

                if decision.kind == OutcomeDecisionKind.SUCCESS:
                    trace.finish(RecoveryRunStatus.SUCCESS)
                    return RecoveryRunResult(
                        trace.status,
                        trace,
                        final_execution_id=execution_id,
                        result=last_result,
                    )

                if decision.kind == OutcomeDecisionKind.VERIFY:
                    # The asynchronous production runtime should resume this run
                    # after targeted evidence arrives rather than busy-wait.
                    self.outcomes.request_outcome_verification(execution_id)
                    trace.finish(RecoveryRunStatus.WAITING_FOR_EVIDENCE)
                    return RecoveryRunResult(
                        trace.status,
                        trace,
                        final_execution_id=execution_id,
                        result=last_result,
                    )

                is_partial = self._partial(decision)
                if is_partial:
                    trace.add(
                        "partial_success",
                        action_id=action_id,
                        execution_id=execution_id,
                        decision=policy.partial_success.value,
                    )
                    if policy.partial_success == PartialSuccessPolicy.ACCEPT:
                        trace.finish(RecoveryRunStatus.PARTIAL_ACCEPTED)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            result=last_result,
                        )
                    if (
                        policy.partial_success == PartialSuccessPolicy.COMPENSATE
                        and policy.rollback_action_id
                    ):
                        decision = OutcomeDecision(
                            kind=OutcomeDecisionKind.ROLLBACK,
                            execution_id=decision.execution_id,
                            action_id=decision.action_id,
                            reason="Partial success policy requests compensation.",
                            assessments=decision.assessments,
                            failed_facts=decision.failed_facts,
                            retry_count=decision.retry_count,
                            rollback_action_id=policy.rollback_action_id,
                        )
                    elif policy.partial_success == PartialSuccessPolicy.REPLAN:
                        trace.finish(RecoveryRunStatus.REPLAN_REQUIRED)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            result=last_result,
                        )

                if decision.kind == OutcomeDecisionKind.RETRY:
                    next_attempt = context.attempt + 1
                    allowed, reason = self._retry_allowed(
                        policy,
                        context,
                        next_attempt=next_attempt,
                    )
                    trace.add(
                        "retry_decision",
                        action_id=action_id,
                        execution_id=execution_id,
                        decision="allow" if allowed else "deny",
                        reason=reason,
                        next_attempt=next_attempt,
                    )
                    if not allowed:
                        trace.finish(RecoveryRunStatus.REPLAN_REQUIRED)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            result=last_result,
                        )

                    parent_execution_id = execution_id
                    context.attempt = next_attempt
                    recovery_steps += 1
                    continue

                if decision.kind == OutcomeDecisionKind.ROLLBACK:
                    rollback_id = decision.rollback_action_id or policy.rollback_action_id
                    if policy.reversibility == ReversibilityClass.IRREVERSIBLE or not rollback_id:
                        trace.add(
                            "rollback_decision",
                            action_id=action_id,
                            execution_id=execution_id,
                            decision="deny",
                            reason=(
                                "Irreversible action has no valid automatic compensation path."
                            ),
                        )
                        trace.finish(RecoveryRunStatus.REPLAN_REQUIRED)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            result=last_result,
                        )

                    if rollback_id not in self.handlers:
                        trace.add(
                            "rollback_decision",
                            action_id=rollback_id,
                            execution_id=execution_id,
                            decision="missing_handler",
                        )
                        trace.finish(RecoveryRunStatus.ROLLBACK_FAILED)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            result=last_result,
                        )

                    trace.add(
                        "rollback_begin",
                        action_id=rollback_id,
                        execution_id=execution_id,
                        decision="compensating_action",
                    )

                    (
                        rollback_exec,
                        rollback_decision,
                        rollback_result,
                        rollback_status,
                    ) = self._run_compensation(
                        rollback_id,
                        trace,
                        deadline=deadline,
                        idempotency_key=idempotency_key,
                        metadata=context.metadata,
                        parent_execution_id=execution_id,
                    )

                    if rollback_status == "success":
                        trace.finish(RecoveryRunStatus.ROLLED_BACK)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            rollback_execution_id=rollback_exec,
                            result=rollback_result,
                        )

                    if rollback_status == "waiting_for_evidence":
                        trace.finish(RecoveryRunStatus.WAITING_FOR_EVIDENCE)
                        return RecoveryRunResult(
                            trace.status,
                            trace,
                            final_execution_id=execution_id,
                            rollback_execution_id=rollback_exec,
                            result=rollback_result,
                        )

                    trace.finish(RecoveryRunStatus.ROLLBACK_FAILED)
                    return RecoveryRunResult(
                        trace.status,
                        trace,
                        final_execution_id=execution_id,
                        rollback_execution_id=rollback_exec,
                        result=rollback_result,
                    )

                trace.finish(RecoveryRunStatus.REPLAN_REQUIRED)
                return RecoveryRunResult(
                    trace.status,
                    trace,
                    final_execution_id=execution_id,
                    result=last_result,
                )

            trace.finish(RecoveryRunStatus.REPLAN_REQUIRED)
            return RecoveryRunResult(
                trace.status,
                trace,
                result=last_result,
            )

        except ExecutionCancelled as exc:
            trace.add(
                "cancelled",
                action_id=context.action_id,
                decision="cancelled",
                reason=str(exc),
            )
            trace.finish(RecoveryRunStatus.CANCELLED)
            return RecoveryRunResult(trace.status, trace)

        except ExecutionDeadlineExceeded as exc:
            trace.add(
                "timeout",
                action_id=context.action_id,
                decision="timed_out",
                reason=str(exc),
            )
            trace.finish(RecoveryRunStatus.TIMED_OUT)
            return RecoveryRunResult(trace.status, trace)
