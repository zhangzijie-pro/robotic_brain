from __future__ import annotations

from robot_brain.core import ActionPacket, SafetyDecision, SkillResult
from robot_brain.learning.trajectory_schema import TaskTrajectory, TrajectoryStepRecord


class TrajectoryRecorder:
    def __init__(
        self,
        task_id: str,
        command: str,
        robot_type: str,
        initial_world_state: dict,
        retrieved_case_ids: list[str] | None = None,
    ) -> None:
        self._trajectory = TaskTrajectory(
            task_id=task_id,
            command=command,
            robot_type=robot_type,
            initial_world_state=initial_world_state,
            retrieved_case_ids=retrieved_case_ids or [],
        )

    def record_step(
        self,
        action_packet: ActionPacket,
        safety_decision: SafetyDecision,
        skill_result: SkillResult | None,
        failure_type: str | None = None,
    ) -> None:
        if not safety_decision.allowed:
            status = "blocked"
        elif skill_result is None:
            status = "pending"
        elif skill_result.status == "success":
            status = "success"
        else:
            status = "failed"

        self._trajectory.add_step(
            TrajectoryStepRecord(
                step_name=action_packet.next_skill,
                skill=action_packet.next_skill,
                action_packet=action_packet.to_dict(),
                safety_decision=safety_decision.to_dict(),
                skill_result=skill_result.details if skill_result else None,
                failure_type=failure_type,
                status=status,
            )
        )

    def finalize(self, final_world_state: dict) -> TaskTrajectory:
        self._trajectory.finish(final_world_state)
        return self._trajectory
