from __future__ import annotations

from robot_brain.core import PlanStep


class PriorityScheduler:
    def order(self, steps: list[PlanStep]) -> list[PlanStep]:
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        return sorted(steps, key=lambda step: risk_rank.get(step.risk, 99))
