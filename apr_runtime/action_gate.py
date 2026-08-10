from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .archive import EvidenceArchive
from .evidence import EvidenceStore
from .models import FactStatus
from .world_state import WorldState


class ActionDecisionKind(str, Enum):
    ALLOW = "allow"
    VERIFY = "verify"
    BLOCK = "block"


class PreconditionState(str, Enum):
    SATISFIED = "satisfied"
    NEEDS_VERIFICATION = "needs_verification"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class FactRequirement:
    """
    Declarative evidence precondition for an action.

    `allowed_values` / `forbidden_values` describe semantic preconditions.
    Freshness/confidence/evidence diversity describe epistemic preconditions.
    """

    fact_key: str
    min_confidence: float = 0.80
    max_age: Optional[float] = None
    allowed_values: Optional[Tuple[Any, ...]] = None
    forbidden_values: Optional[Tuple[Any, ...]] = None
    min_independent_evidence: int = 1
    min_modalities: int = 1
    min_evidence_confidence: float = 0.60
    require_revisitable_asset: bool = False
    contradiction_blocks: bool = True
    inherit_risk_floor: bool = True
    weight: float = 1.0
    description: str = ""


@dataclass(frozen=True)
class ActionSpec:
    id: str
    name: str
    risk: float
    requirements: Tuple[FactRequirement, ...] = ()
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceSummary:
    evidence_count: int
    independent_groups: int
    modalities: int
    sources: Tuple[str, ...]
    modality_names: Tuple[str, ...]
    revisitable_assets: int


@dataclass(frozen=True)
class PreconditionAssessment:
    fact_key: str
    state: PreconditionState
    reason: str
    current_value: Any
    confidence: float
    age: float
    required_confidence: float
    max_age: Optional[float]
    evidence: EvidenceSummary
    urgency: float


@dataclass(frozen=True)
class ActionDecision:
    kind: ActionDecisionKind
    action_id: str
    reason: str
    assessments: Tuple[PreconditionAssessment, ...]
    facts_to_verify: Tuple[str, ...] = ()
    blocking_facts: Tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.kind == ActionDecisionKind.ALLOW


@dataclass
class ActionGatePolicy:
    """
    Runtime-wide safety floor.

    High-risk actions can automatically require stronger confidence and
    independent evidence unless an individual FactRequirement is stricter.
    """

    high_risk_threshold: float = 0.75
    critical_risk_threshold: float = 0.90
    high_risk_min_confidence: float = 0.90
    critical_min_confidence: float = 0.95
    high_risk_min_independent_evidence: int = 2
    critical_min_modalities: int = 1
    block_high_risk_contradictions: bool = True


class ActionReadinessGate:
    """
    Evaluate whether an action has enough *current and evidenced* world state
    to execute.

    The gate never invents missing facts. It returns:
      ALLOW  - all mandatory preconditions are satisfied;
      VERIFY - facts are missing/stale/under-evidenced but potentially fixable;
      BLOCK  - a semantic precondition is false or a blocking contradiction exists.
    """

    def __init__(
        self,
        world: WorldState,
        evidence_store: EvidenceStore,
        *,
        archive: Optional[EvidenceArchive] = None,
        policy: Optional[ActionGatePolicy] = None,
    ) -> None:
        self.world = world
        self.evidence_store = evidence_store
        self.archive = archive
        self.policy = policy or ActionGatePolicy()

    def _effective_min_confidence(
        self,
        action: ActionSpec,
        req: FactRequirement,
    ) -> float:
        floor = req.min_confidence
        if req.inherit_risk_floor and action.risk >= self.policy.high_risk_threshold:
            floor = max(floor, self.policy.high_risk_min_confidence)
        if req.inherit_risk_floor and action.risk >= self.policy.critical_risk_threshold:
            floor = max(floor, self.policy.critical_min_confidence)
        return min(1.0, max(0.0, floor))

    def _effective_min_independent(
        self,
        action: ActionSpec,
        req: FactRequirement,
    ) -> int:
        required = max(1, int(req.min_independent_evidence))
        if req.inherit_risk_floor and action.risk >= self.policy.high_risk_threshold:
            required = max(
                required,
                self.policy.high_risk_min_independent_evidence,
            )
        return required

    def _effective_min_modalities(
        self,
        action: ActionSpec,
        req: FactRequirement,
    ) -> int:
        required = max(1, int(req.min_modalities))
        if req.inherit_risk_floor and action.risk >= self.policy.critical_risk_threshold:
            required = max(required, self.policy.critical_min_modalities)
        return required

    def _evidence_objects(
        self,
        fact_key: str,
        evidence_ids: Sequence[str],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        for evidence_id in evidence_ids:
            ev = self.evidence_store.get(evidence_id)
            if ev is not None:
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
                    # Archive may carry the asset path that in-memory Evidence
                    # does not know about, so merge it.
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

        # Re-reading the same archived image is not independent evidence.
        revisit_of = metadata.get("revisit_of")
        source_asset = metadata.get("source_asset") or item.get("asset_path")
        if revisit_of or source_asset:
            return f"asset:{source_asset or revisit_of}"

        return f"{item.get('modality')}:{item.get('source')}"

    def _summarize_evidence(
        self,
        fact_key: str,
        current_value: Any,
        evidence_ids: Sequence[str],
        *,
        min_confidence: float,
    ) -> EvidenceSummary:
        items = self._evidence_objects(fact_key, evidence_ids)

        supporting = [
            item
            for item in items
            if item.get("observed_value") == current_value
            and float(item.get("confidence", 0.0)) >= min_confidence
        ]

        groups = {self._independence_group(item) for item in supporting}
        modalities = {str(item.get("modality")) for item in supporting if item.get("modality")}
        sources = {str(item.get("source")) for item in supporting if item.get("source")}

        assets = 0
        for item in supporting:
            raw = item.get("asset_path")
            pointer = item.get("pointer")
            if raw and Path(str(raw)).exists():
                assets += 1
            elif pointer and str(pointer).startswith(("frame://", "file://")):
                assets += 1

        return EvidenceSummary(
            evidence_count=len(supporting),
            independent_groups=len(groups),
            modalities=len(modalities),
            sources=tuple(sorted(sources)),
            modality_names=tuple(sorted(modalities)),
            revisitable_assets=assets,
        )

    @staticmethod
    def _verification_urgency(
        action: ActionSpec,
        *,
        confidence_gap: float = 0.0,
        stale: bool = False,
        evidence_gap: int = 0,
        contradicted: bool = False,
    ) -> float:
        score = 0.25 + 0.45 * max(0.0, min(1.0, action.risk))
        score += min(0.20, max(0.0, confidence_gap))
        if stale:
            score += 0.15
        if evidence_gap > 0:
            score += min(0.20, 0.08 * evidence_gap)
        if contradicted:
            score = max(score, 0.95)
        return min(1.0, score)

    def assess_requirement(
        self,
        action: ActionSpec,
        req: FactRequirement,
        *,
        now: Optional[float] = None,
    ) -> PreconditionAssessment:
        now = time.time() if now is None else float(now)
        fact = self.world.get(req.fact_key, now=now)

        min_conf = self._effective_min_confidence(action, req)
        min_independent = self._effective_min_independent(action, req)
        min_modalities = self._effective_min_modalities(action, req)

        summary = self._summarize_evidence(
            req.fact_key,
            fact.value,
            fact.evidence_ids,
            min_confidence=req.min_evidence_confidence,
        )

        if fact.status == FactStatus.CONTRADICTED:
            hard_block = req.contradiction_blocks or (
                action.risk >= self.policy.high_risk_threshold
                and self.policy.block_high_risk_contradictions
            )
            state = (
                PreconditionState.BLOCKED if hard_block else PreconditionState.NEEDS_VERIFICATION
            )
            return PreconditionAssessment(
                fact_key=req.fact_key,
                state=state,
                reason="Current world-state fact is contradicted.",
                current_value=fact.value,
                confidence=fact.confidence,
                age=fact.age(now),
                required_confidence=min_conf,
                max_age=req.max_age,
                evidence=summary,
                urgency=self._verification_urgency(
                    action,
                    contradicted=True,
                ),
            )

        if fact.status == FactStatus.UNKNOWN or fact.value is None:
            return PreconditionAssessment(
                fact_key=req.fact_key,
                state=PreconditionState.NEEDS_VERIFICATION,
                reason="Required fact is unknown.",
                current_value=fact.value,
                confidence=fact.confidence,
                age=fact.age(now),
                required_confidence=min_conf,
                max_age=req.max_age,
                evidence=summary,
                urgency=self._verification_urgency(action),
            )

        if req.forbidden_values is not None and fact.value in req.forbidden_values:
            return PreconditionAssessment(
                fact_key=req.fact_key,
                state=PreconditionState.BLOCKED,
                reason="Current fact value violates a forbidden action precondition.",
                current_value=fact.value,
                confidence=fact.confidence,
                age=fact.age(now),
                required_confidence=min_conf,
                max_age=req.max_age,
                evidence=summary,
                urgency=1.0,
            )

        if req.allowed_values is not None and fact.value not in req.allowed_values:
            return PreconditionAssessment(
                fact_key=req.fact_key,
                state=PreconditionState.BLOCKED,
                reason="Current fact value does not satisfy the action precondition.",
                current_value=fact.value,
                confidence=fact.confidence,
                age=fact.age(now),
                required_confidence=min_conf,
                max_age=req.max_age,
                evidence=summary,
                urgency=1.0,
            )

        age = fact.age(now)
        stale = fact.status == FactStatus.STALE or (req.max_age is not None and age > req.max_age)
        confidence_gap = max(0.0, min_conf - fact.confidence)
        evidence_gap = max(
            0,
            min_independent - summary.independent_groups,
        )
        modality_gap = max(
            0,
            min_modalities - summary.modalities,
        )

        needs_asset = req.require_revisitable_asset and summary.revisitable_assets < 1

        if stale:
            reason = "Required fact is stale for this action."
        elif confidence_gap > 0:
            reason = "Required fact confidence is below the action threshold."
        elif evidence_gap > 0:
            reason = (
                "Action requires more independent supporting evidence "
                f"({summary.independent_groups}/{min_independent})."
            )
        elif modality_gap > 0:
            reason = (
                "Action requires evidence from more distinct modalities "
                f"({summary.modalities}/{min_modalities})."
            )
        elif needs_asset:
            reason = "Action requires at least one revisitable evidence asset."
        else:
            return PreconditionAssessment(
                fact_key=req.fact_key,
                state=PreconditionState.SATISFIED,
                reason="Action precondition is satisfied.",
                current_value=fact.value,
                confidence=fact.confidence,
                age=age,
                required_confidence=min_conf,
                max_age=req.max_age,
                evidence=summary,
                urgency=0.0,
            )

        return PreconditionAssessment(
            fact_key=req.fact_key,
            state=PreconditionState.NEEDS_VERIFICATION,
            reason=reason,
            current_value=fact.value,
            confidence=fact.confidence,
            age=age,
            required_confidence=min_conf,
            max_age=req.max_age,
            evidence=summary,
            urgency=self._verification_urgency(
                action,
                confidence_gap=confidence_gap,
                stale=stale,
                evidence_gap=evidence_gap + modality_gap + (1 if needs_asset else 0),
            ),
        )

    def evaluate(
        self,
        action: ActionSpec,
        *,
        now: Optional[float] = None,
    ) -> ActionDecision:
        assessments = tuple(
            self.assess_requirement(action, req, now=now) for req in action.requirements
        )

        blocked = tuple(a.fact_key for a in assessments if a.state == PreconditionState.BLOCKED)
        verify = tuple(
            a.fact_key for a in assessments if a.state == PreconditionState.NEEDS_VERIFICATION
        )

        if blocked:
            return ActionDecision(
                kind=ActionDecisionKind.BLOCK,
                action_id=action.id,
                reason="One or more action preconditions are false or contradicted.",
                assessments=assessments,
                facts_to_verify=verify,
                blocking_facts=blocked,
            )

        if verify:
            return ActionDecision(
                kind=ActionDecisionKind.VERIFY,
                action_id=action.id,
                reason="Action is not ready; additional evidence is required.",
                assessments=assessments,
                facts_to_verify=verify,
            )

        return ActionDecision(
            kind=ActionDecisionKind.ALLOW,
            action_id=action.id,
            reason="All declared evidence preconditions are satisfied.",
            assessments=assessments,
        )
