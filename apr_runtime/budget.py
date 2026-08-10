from __future__ import annotations

from .models import Budget, PerceptualAction


class BudgetController:
    def __init__(self, budget: Budget) -> None:
        self.budget = budget

    def affordable(self, action: PerceptualAction) -> bool:
        return self.budget.can_afford(action.estimated_cost)

    def commit(self, action: PerceptualAction) -> None:
        if action.mode.value != "no_observation":
            self.budget.spend(action.estimated_cost)
