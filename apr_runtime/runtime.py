from __future__ import annotations

from typing import Dict, Optional

from .adapters import BaseAdapter
from .budget import BudgetController
from .evidence import EvidenceStore
from .models import (
    Budget,
    Evidence,
    Goal,
    Modality,
    PerceptualAction,
    ReadingMode,
)
from .policy import PolicyController
from .world_state import WorldState


class APRRuntime:
    def __init__(
        self,
        world: WorldState,
        evidence_store: EvidenceStore,
        policy: PolicyController,
        budget: Budget,
        adapters: Dict[Modality, BaseAdapter],
    ) -> None:
        self.world = world
        self.evidence_store = evidence_store
        self.policy = policy
        self.budget_controller = BudgetController(budget)
        self.adapters = adapters
        self.history = []

        # Adapters may declare native state schema (TTL/volatility) without
        # coupling APRRuntime to modality-specific fact names.
        for adapter in self.adapters.values():
            configure = getattr(adapter, "configure_world", None)
            if callable(configure):
                configure(self.world)

    @property
    def budget(self) -> Budget:
        return self.budget_controller.budget

    def decide(self, goal: Goal) -> PerceptualAction:
        return self.policy.decide(self.world, goal)

    def execute(self, action: PerceptualAction) -> Optional[Evidence]:
        self.history.append(action)

        if action.mode == ReadingMode.NO_OBSERVATION:
            return None

        if action.mode == ReadingMode.EPISTEMIC_ACTION:
            # Hook only in v0.1. A later version can call camera/GUI/robot tools.
            return None

        if action.modality is None or action.modality not in self.adapters:
            raise RuntimeError(f"No adapter for modality: {action.modality}")

        if not self.budget_controller.affordable(action):
            raise RuntimeError("Perceptual action exceeds remaining budget.")

        self.budget_controller.commit(action)
        evidence = self.adapters[action.modality].observe(action)

        fact = self.world.get(action.target)
        if action.mode == ReadingMode.REVISIT and fact.status.value == "contradicted":
            self.world.resolve_conflict(action.target, evidence)
        else:
            self.world.revise(evidence)

        return evidence

    def step(self, goal: Goal):
        action = self.decide(goal)
        evidence = self.execute(action)
        return action, evidence
