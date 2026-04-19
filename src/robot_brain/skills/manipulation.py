from __future__ import annotations

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class EstimateGraspPoseSkill:
    name = "estimate_grasp_pose"
    default_risk = "medium"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.estimate_grasp_pose(
            object_id=str(step.args.get("object_id", "unknown_object")),
            args=step.args,
        )


class GraspSkill:
    name = "grasp"
    default_risk = "high"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.grasp(
            object_id=str(step.args.get("object_id", "unknown_object")),
            args=step.args,
        )
