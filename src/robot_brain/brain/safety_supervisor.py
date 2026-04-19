from __future__ import annotations

from robot_brain.brain.world_model import WorldModel
from robot_brain.core import PlanStep, SafetyDecision


class SafetySupervisor:
    def check(self, step: PlanStep, world: WorldModel) -> SafetyDecision:
        robot_state = world.robot_state or {}
        human_state = world.human_state or {}

        if robot_state.get("emergency_stop"):
            return SafetyDecision(False, "emergency stop is active")

        if step.risk == "high":
            distance = float(human_state.get("distance_m", 99.0))
            if distance < 0.8:
                return SafetyDecision(False, "human is too close")

        if step.skill == "grasp" and any("edge" in risk for risk in world.risks):
            return SafetyDecision(
                allowed=True,
                reason="allowed with slow grasp because table-edge risk was detected",
                required_confirmation=False,
            )

        return SafetyDecision(True, "allowed")

