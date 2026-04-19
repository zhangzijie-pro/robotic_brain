from __future__ import annotations

from robot_brain.core import SkillResult


class ReplanTrigger:
    def should_replan(self, result: SkillResult | None, world_delta: dict | None = None) -> bool:
        if result and result.status != "success":
            return True
        if world_delta and world_delta.get("target_lost"):
            return True
        if world_delta and world_delta.get("safety_state_changed"):
            return True
        return False
