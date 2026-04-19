from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class HumanInteractionSkill:
    name = "handover_to_human"
    default_risk = "high"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.handover_to_human(
            recipient=str(step.args.get("recipient", "user")),
            args=step.args,
        )
