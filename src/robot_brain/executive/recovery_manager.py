from __future__ import annotations

from robot_brain.core import PlanStep, SkillResult


class RecoveryManager:
    def propose_recovery(self, failed_result: SkillResult) -> list[PlanStep]:
        return [
            PlanStep(
                name="observe_after_failure",
                skill="observe",
                args={"reason": failed_result.status, "failed_skill": failed_result.skill},
                risk="low",
            )
        ]
