from __future__ import annotations

from robot_brain.core import PlanStep


class Arbitration:
    """Chooses which candidate command owns the robot next."""

    def select(self, candidates: list[PlanStep]) -> PlanStep | None:
        if not candidates:
            return None
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        return sorted(candidates, key=lambda step: risk_rank.get(step.risk, 99))[0]
