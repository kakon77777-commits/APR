from __future__ import annotations

from math import isfinite
from typing import Any, Dict, Optional

from .evidence import EvidenceStore
from .models import Evidence, FactState, FactStatus


class WorldState:
    """
    Current structured belief, not an append-only event log.

    v0.2 adds volatile facts. A volatile fact (foreground window title,
    cursor position, screen-change score, etc.) is expected to change and
    therefore should not be marked CONTRADICTED just because a later
    high-confidence observation differs.
    """

    def __init__(self, evidence_store: EvidenceStore) -> None:
        self.evidence_store = evidence_store
        self.facts: Dict[str, FactState] = {}

    @staticmethod
    def _validate_ttl(ttl: float) -> None:
        if not isfinite(ttl) or ttl < 0.0:
            raise ValueError("ttl must be a finite non-negative value")

    def ensure_fact(
        self,
        key: str,
        ttl: Optional[float] = None,
        volatile: Optional[bool] = None,
    ) -> FactState:
        if ttl is not None:
            self._validate_ttl(ttl)
        if key not in self.facts:
            self.facts[key] = FactState(
                key=key,
                ttl=60.0 if ttl is None else ttl,
                volatile=False if volatile is None else volatile,
            )
        else:
            if ttl is not None:
                self.facts[key].ttl = ttl
            if volatile is not None:
                self.facts[key].volatile = volatile
        return self.facts[key]

    def configure_fact(
        self,
        key: str,
        *,
        ttl: Optional[float] = None,
        volatile: Optional[bool] = None,
    ) -> FactState:
        if ttl is not None:
            self._validate_ttl(ttl)
        fact = self.ensure_fact(key)
        if ttl is not None:
            fact.ttl = ttl
        if volatile is not None:
            fact.volatile = volatile
        return fact

    def get(self, key: str, now: Optional[float] = None) -> FactState:
        fact = self.ensure_fact(key)
        fact.refresh_status(now=now)
        return fact

    def revise(self, evidence: Evidence, conflict_margin: float = 0.12) -> FactState:
        self.evidence_store.add(evidence)
        fact = self.ensure_fact(evidence.claim_key)

        prior_value = fact.value
        prior_conf = fact.confidence
        conflicting = (
            not fact.volatile
            and prior_value is not None
            and prior_value != evidence.observed_value
            and prior_conf >= 0.7
            and evidence.confidence >= 0.7
        )

        fact.evidence_ids.append(evidence.id)
        fact.version += 1

        if conflicting:
            # Strong disagreement in a non-volatile claim should not silently
            # become last-write-wins.
            fact.status = FactStatus.CONTRADICTED
            fact.confidence = max(
                0.0,
                min(prior_conf, evidence.confidence) - conflict_margin,
            )
            return fact

        if prior_value == evidence.observed_value and prior_value is not None:
            fact.confidence = min(
                0.999,
                1.0 - (1.0 - prior_conf) * (1.0 - evidence.confidence),
            )
        else:
            fact.value = evidence.observed_value
            fact.confidence = evidence.confidence

        fact.last_verified = evidence.timestamp
        fact.refresh_status(now=evidence.timestamp)
        return fact

    def resolve_conflict(self, key: str, evidence: Evidence) -> FactState:
        """
        A targeted revisit may resolve a contradiction if the new evidence
        is high-confidence. Evidence provenance is still preserved.
        """
        self.evidence_store.add(evidence)
        fact = self.ensure_fact(key)
        fact.evidence_ids.append(evidence.id)
        fact.version += 1

        if evidence.confidence >= 0.85:
            fact.value = evidence.observed_value
            fact.confidence = evidence.confidence
            fact.last_verified = evidence.timestamp
            fact.status = FactStatus.KNOWN
        else:
            fact.status = FactStatus.UNCERTAIN
            fact.confidence = max(fact.confidence, evidence.confidence)

        return fact

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        out = {}
        for key, fact in self.facts.items():
            fact.refresh_status()
            out[key] = {
                "value": fact.value,
                "confidence": round(fact.confidence, 3),
                "status": fact.status.value,
                "age": round(fact.age(), 3),
                "ttl": fact.ttl,
                "version": fact.version,
                "evidence_count": len(fact.evidence_ids),
                "volatile": fact.volatile,
            }
        return out
