from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .archive import EvidenceArchive
from .world_state import WorldState


class QueryScope(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"


class QueryDecisionKind(str, Enum):
    ANSWER_FROM_STATE = "answer_from_state"
    REFRESH_CURRENT = "refresh_current"
    HISTORICAL_REVISIT = "historical_revisit"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PerceptualQuery:
    required_facts: tuple[str, ...]
    scope: QueryScope = QueryScope.CURRENT
    question: str = ""
    min_confidence: float = 0.8


@dataclass(frozen=True)
class QueryDecision:
    kind: QueryDecisionKind
    facts: tuple[str, ...]
    reason: str


class QueryRouter:
    """Structured current-vs-historical query routing.

    It deliberately avoids pretending an NLP classifier is necessary for the
    runtime. Upstream planners can supply explicit time scope.
    """

    def __init__(
        self,
        world: WorldState,
        *,
        archive: Optional[EvidenceArchive] = None,
    ) -> None:
        self.world = world
        self.archive = archive

    def route(self, query: PerceptualQuery) -> QueryDecision:
        if not query.required_facts:
            return QueryDecision(
                QueryDecisionKind.BLOCKED,
                (),
                "Query does not declare required facts.",
            )

        if query.scope == QueryScope.HISTORICAL:
            if self.archive is None:
                return QueryDecision(
                    QueryDecisionKind.BLOCKED,
                    query.required_facts,
                    "Historical query requires an EvidenceArchive.",
                )
            missing = [
                fact
                for fact in query.required_facts
                if self.archive.best_for_claim(fact, require_asset=True) is None
            ]
            if missing:
                return QueryDecision(
                    QueryDecisionKind.BLOCKED,
                    tuple(missing),
                    "Historical evidence with a revisitable asset is unavailable.",
                )
            return QueryDecision(
                QueryDecisionKind.HISTORICAL_REVISIT,
                query.required_facts,
                "Historical evidence is available for targeted re-reading.",
            )

        insufficient = []
        for fact_key in query.required_facts:
            fact = self.world.get(fact_key)
            if fact.status.value != "known" or fact.confidence < query.min_confidence:
                insufficient.append(fact_key)
        if insufficient:
            return QueryDecision(
                QueryDecisionKind.REFRESH_CURRENT,
                tuple(insufficient),
                "Current world state is insufficient or stale.",
            )
        return QueryDecision(
            QueryDecisionKind.ANSWER_FROM_STATE,
            query.required_facts,
            "Current world state is fresh and sufficiently confident.",
        )
