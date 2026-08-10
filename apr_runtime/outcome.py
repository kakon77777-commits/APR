from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .action_gate import EvidenceSummary
from .archive import EvidenceArchive
from .evidence import EvidenceStore
from .models import FactStatus
from .world_state import WorldState


class OutcomeDecisionKind(str, Enum):
    SUCCESS = "success"
    VERIFY = "verify"
    RETRY = "retry"
    REPLAN = "replan"
    ROLLBACK = "rollback"
    FAILED = "failed"


class PostconditionState(str, Enum):
    SATISFIED = "satisfied"
    NEEDS_VERIFICATION = "needs_verification"
    FAILED = "failed"
    CONTRADICTED = "contradicted"


@dataclass(frozen=True)
class PostconditionRequirement:
    fact_key: str
    expected_values: Optional[Tuple[Any, ...]] = None
    forbidden_values: Optional[Tuple[Any, ...]] = None
    min_confidence: float = 0.80
    min_independent_evidence: int = 1
    min_modalities: int = 1
    min_evidence_confidence: float = 0.60
    require_post_action_evidence: bool = True
    must_change_from_pre_state: bool = False
    max_observation_age: Optional[float] = None
    description: str = ""


@dataclass(frozen=True)
class ActionOutcomeSpec:
    action_id: str
    postconditions: Tuple[PostconditionRequirement, ...]
    verification_timeout: float = 5.0
    max_retries: int = 1
    retry_safe: bool = True
    rollback_action_id: Optional[str] = None
    rollback_on_failure: bool = False
    description: str = ""


@dataclass(frozen=True)
class PostconditionAssessment:
    fact_key: str
    state: PostconditionState
    reason: str
    current_value: Any
    pre_value: Any
    confidence: float
    evidence: EvidenceSummary
    post_action_evidence_count: int
    age_since_action: float


@dataclass(frozen=True)
class OutcomeDecision:
    kind: OutcomeDecisionKind
    execution_id: str
    action_id: str
    reason: str
    assessments: Tuple[PostconditionAssessment, ...]
    facts_to_verify: Tuple[str, ...] = ()
    failed_facts: Tuple[str, ...] = ()
    retry_count: int = 0
    rollback_action_id: Optional[str] = None


class ActionOutcomeVerifier:
    """
    Verify effects from observed post-action state.

    Critical invariant:
    expected transitions are not written into WorldState as facts.
    Success requires observed supporting evidence after execution unless a
    PostconditionRequirement explicitly disables that requirement.
    """

    def __init__(
        self,
        world: WorldState,
        evidence_store: EvidenceStore,
        *,
        archive: Optional[EvidenceArchive] = None,
    ) -> None:
        self.world = world
        self.evidence_store = evidence_store
        self.archive = archive

    def _evidence_objects(
        self,
        fact_key: str,
        evidence_ids: Sequence[str],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        seen = set()

        for evidence_id in evidence_ids:
            ev = self.evidence_store.get(evidence_id)
            if ev is None:
                continue
            out.append(
                {
                    "id": ev.id,
                    "claim_key": ev.claim_key,
                    "observed_value": ev.observed_value,
                    "modality": ev.modality.value,
                    "source": ev.source,
                    "confidence": ev.confidence,
                    "timestamp": ev.timestamp,
                    "pointer": ev.pointer,
                    "asset_path": None,
                    "metadata": dict(ev.metadata),
                }
            )
            seen.add(ev.id)

        if self.archive is not None:
            for row in self.archive.by_ids(evidence_ids):
                if row["id"] in seen:
                    for item in out:
                        if item["id"] == row["id"]:
                            item["asset_path"] = row.get("asset_path")
                            break
                    continue
                out.append(row)
                seen.add(row["id"])

        return [item for item in out if item.get("claim_key") == fact_key]

    @staticmethod
    def _independence_group(item: Dict[str, Any]) -> str:
        metadata = item.get("metadata") or {}
        explicit = metadata.get("independence_group")
        if explicit:
            return str(explicit)

        source_asset = metadata.get("source_asset") or item.get("asset_path")
        revisit_of = metadata.get("revisit_of")
        if source_asset or revisit_of:
            return f"asset:{source_asset or revisit_of}"

        return f"{item.get('modality')}:{item.get('source')}"

    def _summary(
        self,
        req: PostconditionRequirement,
        current_value: Any,
        evidence_ids: Sequence[str],
        *,
        executed_at: float,
    ) -> tuple[EvidenceSummary, int]:
        items = self._evidence_objects(req.fact_key, evidence_ids)

        supporting = [
            item
            for item in items
            if item.get("observed_value") == current_value
            and float(item.get("confidence", 0.0)) >= req.min_evidence_confidence
        ]
        post = [item for item in supporting if float(item.get("timestamp", 0.0)) >= executed_at]

        groups = {self._independence_group(item) for item in post}
        modalities = {str(item.get("modality")) for item in post if item.get("modality")}
        sources = {str(item.get("source")) for item in post if item.get("source")}
        assets = sum(1 for item in post if item.get("asset_path") or item.get("pointer"))

        return (
            EvidenceSummary(
                evidence_count=len(post),
                independent_groups=len(groups),
                modalities=len(modalities),
                sources=tuple(sorted(sources)),
                modality_names=tuple(sorted(modalities)),
                revisitable_assets=assets,
            ),
            len(post),
        )

    def assess(
        self,
        req: PostconditionRequirement,
        *,
        executed_at: float,
        pre_value: Any,
        now: Optional[float] = None,
    ) -> PostconditionAssessment:
        now = time.time() if now is None else float(now)
        fact = self.world.get(req.fact_key, now=now)
        summary, post_count = self._summary(
            req,
            fact.value,
            fact.evidence_ids,
            executed_at=executed_at,
        )

        age_since_action = max(0.0, now - executed_at)

        if fact.status == FactStatus.CONTRADICTED:
            return PostconditionAssessment(
                fact_key=req.fact_key,
                state=PostconditionState.CONTRADICTED,
                reason="Post-action world-state fact is contradicted.",
                current_value=fact.value,
                pre_value=pre_value,
                confidence=fact.confidence,
                evidence=summary,
                post_action_evidence_count=post_count,
                age_since_action=age_since_action,
            )

        if fact.value is None or fact.status == FactStatus.UNKNOWN:
            return PostconditionAssessment(
                fact_key=req.fact_key,
                state=PostconditionState.NEEDS_VERIFICATION,
                reason="Postcondition fact has not been observed.",
                current_value=fact.value,
                pre_value=pre_value,
                confidence=fact.confidence,
                evidence=summary,
                post_action_evidence_count=post_count,
                age_since_action=age_since_action,
            )

        if req.expected_values is not None and fact.value not in req.expected_values:
            # If there is no post-action evidence yet, we cannot use a pre-action
            # value to claim the action failed; first request verification.
            if req.require_post_action_evidence and post_count == 0:
                state = PostconditionState.NEEDS_VERIFICATION
                reason = (
                    "Current value does not match the expected postcondition, "
                    "but no post-action evidence has verified that value yet."
                )
            else:
                state = PostconditionState.FAILED
                reason = "Observed post-action value does not match expectation."
            return PostconditionAssessment(
                req.fact_key,
                state,
                reason,
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if req.forbidden_values is not None and fact.value in req.forbidden_values:
            if req.require_post_action_evidence and post_count == 0:
                state = PostconditionState.NEEDS_VERIFICATION
                reason = (
                    "Current value is forbidden, but no post-action evidence "
                    "has confirmed it after execution."
                )
            else:
                state = PostconditionState.FAILED
                reason = "Observed post-action value violates the postcondition."
            return PostconditionAssessment(
                req.fact_key,
                state,
                reason,
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if req.must_change_from_pre_state and fact.value == pre_value:
            if req.require_post_action_evidence and post_count == 0:
                state = PostconditionState.NEEDS_VERIFICATION
                reason = "State transition has not yet been verified after action."
            else:
                state = PostconditionState.FAILED
                reason = "Expected state transition did not occur."
            return PostconditionAssessment(
                req.fact_key,
                state,
                reason,
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if req.require_post_action_evidence and post_count == 0:
            return PostconditionAssessment(
                req.fact_key,
                PostconditionState.NEEDS_VERIFICATION,
                "Matching state exists, but it is supported only by pre-action evidence.",
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if fact.confidence < req.min_confidence:
            return PostconditionAssessment(
                req.fact_key,
                PostconditionState.NEEDS_VERIFICATION,
                "Post-action confidence is below the required threshold.",
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if summary.independent_groups < max(1, req.min_independent_evidence):
            return PostconditionAssessment(
                req.fact_key,
                PostconditionState.NEEDS_VERIFICATION,
                "Postcondition needs more independent supporting evidence.",
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if summary.modalities < max(1, req.min_modalities):
            return PostconditionAssessment(
                req.fact_key,
                PostconditionState.NEEDS_VERIFICATION,
                "Postcondition needs evidence from more modalities.",
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        if (
            req.max_observation_age is not None
            and fact.last_verified > 0
            and now - fact.last_verified > req.max_observation_age
        ):
            return PostconditionAssessment(
                req.fact_key,
                PostconditionState.NEEDS_VERIFICATION,
                "Post-action evidence is too old for this verification.",
                fact.value,
                pre_value,
                fact.confidence,
                summary,
                post_count,
                age_since_action,
            )

        return PostconditionAssessment(
            req.fact_key,
            PostconditionState.SATISFIED,
            "Postcondition is supported by sufficient post-action evidence.",
            fact.value,
            pre_value,
            fact.confidence,
            summary,
            post_count,
            age_since_action,
        )

    def decide(
        self,
        spec: ActionOutcomeSpec,
        *,
        execution_id: str,
        executed_at: float,
        pre_state: Dict[str, Any],
        retry_count: int,
        now: Optional[float] = None,
    ) -> OutcomeDecision:
        now = time.time() if now is None else float(now)
        assessments = tuple(
            self.assess(
                req,
                executed_at=executed_at,
                pre_value=pre_state.get(req.fact_key),
                now=now,
            )
            for req in spec.postconditions
        )

        contradicted = tuple(
            a.fact_key for a in assessments if a.state == PostconditionState.CONTRADICTED
        )
        failed = tuple(a.fact_key for a in assessments if a.state == PostconditionState.FAILED)
        verify = tuple(
            a.fact_key for a in assessments if a.state == PostconditionState.NEEDS_VERIFICATION
        )

        if not contradicted and not failed and not verify:
            return OutcomeDecision(
                OutcomeDecisionKind.SUCCESS,
                execution_id,
                spec.action_id,
                "All postconditions are verified.",
                assessments,
                retry_count=retry_count,
            )

        timed_out = (now - executed_at) >= max(0.0, spec.verification_timeout)

        if verify and not failed and not contradicted and not timed_out:
            return OutcomeDecision(
                OutcomeDecisionKind.VERIFY,
                execution_id,
                spec.action_id,
                "Post-action evidence is incomplete; continue targeted verification.",
                assessments,
                facts_to_verify=verify,
                retry_count=retry_count,
            )

        failure_facts = tuple(dict.fromkeys((*failed, *contradicted, *verify)))

        if spec.rollback_on_failure and spec.rollback_action_id:
            return OutcomeDecision(
                OutcomeDecisionKind.ROLLBACK,
                execution_id,
                spec.action_id,
                "Postconditions failed; rollback policy is configured.",
                assessments,
                failed_facts=failure_facts,
                retry_count=retry_count,
                rollback_action_id=spec.rollback_action_id,
            )

        if spec.retry_safe and retry_count < max(0, spec.max_retries):
            return OutcomeDecision(
                OutcomeDecisionKind.RETRY,
                execution_id,
                spec.action_id,
                "Postconditions were not achieved; retry is permitted.",
                assessments,
                failed_facts=failure_facts,
                retry_count=retry_count,
            )

        return OutcomeDecision(
            OutcomeDecisionKind.REPLAN,
            execution_id,
            spec.action_id,
            "Postconditions were not achieved and retry/rollback is unavailable.",
            assessments,
            failed_facts=failure_facts,
            retry_count=retry_count,
        )
