from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class ObserveSkill:
    name = "observe"
    default_risk = "low"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.observe(step.args)


class InspectionSkill:
    name = "inspection"
    default_risk = "medium"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.inspect(
            target=str(step.args.get("target", "current_area")),
            args=step.args,
        )
