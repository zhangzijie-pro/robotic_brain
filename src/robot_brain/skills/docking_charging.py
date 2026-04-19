from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class DockingChargingSkill:
    name = "dock_charge"
    default_risk = "medium"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.dock_charge(
            station_id=str(step.args.get("station_id", "default_dock")),
            args=step.args,
        )
