from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .models import Evidence


class EvidenceStore:
    def __init__(self) -> None:
        self._items: Dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> str:
        self._items[evidence.id] = evidence
        return evidence.id

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._items.get(evidence_id)

    def for_claim(self, claim_key: str) -> List[Evidence]:
        return sorted(
            [e for e in self._items.values() if e.claim_key == claim_key],
            key=lambda e: e.timestamp,
        )

    def all(self) -> Iterable[Evidence]:
        return self._items.values()
