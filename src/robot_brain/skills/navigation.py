from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class NavigationSkill:
    name = "navigate_to"
    default_risk = "medium"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.navigate_to(
            location_hint=str(step.args.get("location_hint", "unknown")),
            args=step.args,
        )


class DroneFlyToSkill:
    name = "fly_to"
    default_risk = "high"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        pose = step.args.get("pose", {})
        if not isinstance(pose, dict):
            pose = {"raw": pose}
        return await robot_bridge.fly_to(pose=pose, args=step.args)
