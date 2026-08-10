from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Set

from .archive import EvidenceArchive
from .event_ledger import EventLedger
from .world_state import WorldState


@dataclass
class RetentionPolicy:
    event_keep_seconds: float = 86400.0
    event_keep_significance_at_least: float = 0.75
    evidence_keep_seconds: float = 7 * 86400.0
    evidence_keep_confidence_at_least: float = 0.90
    delete_unreferenced_assets: bool = True


@dataclass
class RetentionReport:
    events_deleted: int = 0
    evidence_deleted: int = 0
    assets_deleted: int = 0


class RetentionManager:
    def __init__(
        self,
        event_ledger: EventLedger,
        evidence_archive: EvidenceArchive,
        world: Optional[WorldState] = None,
        *,
        policy: Optional[RetentionPolicy] = None,
    ) -> None:
        self.event_ledger = event_ledger
        self.evidence_archive = evidence_archive
        self.world = world
        self.policy = policy or RetentionPolicy()

    def protected_evidence_ids(self) -> Set[str]:
        if self.world is None:
            return set()
        protected: Set[str] = set()
        for fact in self.world.facts.values():
            protected.update(fact.evidence_ids)
        return protected

    def run(self, *, now: Optional[float] = None) -> RetentionReport:
        now = time.time() if now is None else float(now)
        events_deleted = self.event_ledger.compact(
            older_than=now - self.policy.event_keep_seconds,
            keep_significance_at_least=self.policy.event_keep_significance_at_least,
        )
        evidence_deleted, assets_deleted = self.evidence_archive.compact(
            older_than=now - self.policy.evidence_keep_seconds,
            keep_confidence_at_least=self.policy.evidence_keep_confidence_at_least,
            protected_ids=self.protected_evidence_ids(),
            delete_unreferenced_assets=self.policy.delete_unreferenced_assets,
        )
        return RetentionReport(
            events_deleted=events_deleted,
            evidence_deleted=evidence_deleted,
            assets_deleted=assets_deleted,
        )
