from __future__ import annotations

from robot_brain.brain.world_model import WorldModel
from robot_brain.config import create_default_robot_profile
from robot_brain.core import PlanStep, RobotProfile


class TaskPlanner:
    def create_plan(
        self,
        world: WorldModel,
        robot_profile: RobotProfile | None = None,
    ) -> list[PlanStep]:
        robot_profile = robot_profile or create_default_robot_profile()
        target = world.find_target_object()
        if not target:
            return [
                PlanStep(
                    name="observe_scene",
                    skill="observe",
                    args={"reason": "target object not found"},
                    risk="low",
                )
            ]

        object_id, payload = target
        name = payload.get("name", object_id)
        if robot_profile.robot_type == "drone" or robot_profile.has_capability("fly_to"):
            return self._create_inspection_or_drone_plan(object_id, payload, name)

        if not robot_profile.has_capability("grasp"):
            return [
                PlanStep(
                    name="inspect_target",
                    skill="inspection",
                    args={"target": object_id, "object_name": name},
                    risk="medium",
                )
            ]

        return [
            PlanStep(
                name="verify_target",
                skill="observe",
                args={"object_id": object_id, "object_name": name},
                risk="low",
            ),
            PlanStep(
                name="navigate_to_target_area",
                skill="navigate_to",
                args={"location_hint": payload.get("location_hint", "on_table")},
                risk="medium",
            ),
            PlanStep(
                name="estimate_grasp",
                skill="estimate_grasp_pose",
                args={"object_id": object_id},
                risk="medium",
            ),
            PlanStep(
                name="grasp_target",
                skill="grasp",
                args={"object_id": object_id},
                risk="high",
            ),
            PlanStep(
                name="handover",
                skill="handover_to_human",
                args={"recipient": "user"},
                risk="high",
            ),
        ]

    def _create_inspection_or_drone_plan(
        self,
        object_id: str,
        payload: dict,
        name: object,
    ) -> list[PlanStep]:
        location_hint = payload.get("location_hint", "target_area")
        return [
            PlanStep(
                name="verify_target",
                skill="observe",
                args={"object_id": object_id, "object_name": name},
                risk="low",
            ),
            PlanStep(
                name="approach_inspection_area",
                skill="fly_to",
                args={
                    "pose": {"semantic_target": location_hint},
                    "object_id": object_id,
                },
                risk="high",
            ),
            PlanStep(
                name="inspect_target",
                skill="inspection",
                args={"target": object_id, "object_name": name},
                risk="medium",
            ),
        ]
