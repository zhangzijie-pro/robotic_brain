from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class FollowEscortSkill:
    name = "follow_escort"
    default_risk = "medium"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.follow_escort(
            target=str(step.args.get("target", "user")),
            args=step.args,
        )
