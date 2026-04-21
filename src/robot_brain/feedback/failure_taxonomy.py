from __future__ import annotations

from robot_brain.core import ActionPacket, SafetyDecision, SkillResult
from robot_brain.learning.trajectory_schema import TaskTrajectory


FAILURE_TYPES = [
    "perception_failure",
    "grounding_failure",
    "world_model_stale",
    "planning_failure",
    "skill_execution_failure",
    "safety_rejection",
    "human_ambiguity",
    "environment_out_of_distribution",
    "hardware_bridge_failure",
]


def classify_trajectory_failure(trajectory: TaskTrajectory) -> str | None:
    for step in trajectory.steps:
        if step.status == "blocked":
            return "safety_rejection"

        skill_result = step.skill_result or {}
        error = str(skill_result.get("command_result", {}).get("error", "")).lower()
        error_type = str(
            skill_result.get("command_result", {}).get("error_type", "")
        ).lower()

        if "not wired yet" in error or "runtimeerror" in error_type:
            return "hardware_bridge_failure"

        if step.status == "failed" and step.skill in {"observe", "inspection"}:
            return "perception_failure"

        if step.status == "failed" and step.skill in {"navigate_to", "fly_to"}:
            return "planning_failure"

        if step.status == "failed":
            return "skill_execution_failure"

    if not trajectory.final_world_state.get("objects"):
        return "grounding_failure"

    if trajectory.final_world_state.get("scene_summary") is None:
        return "world_model_stale"

    return None


def classify_step_failure(
    action_packet: ActionPacket,
    safety_decision: SafetyDecision,
    skill_result: SkillResult | None,
) -> str | None:
    if not safety_decision.allowed:
        return "safety_rejection"
    if skill_result is None:
        return None

    error = str(skill_result.details.get("command_result", {}).get("error", "")).lower()
    error_type = str(
        skill_result.details.get("command_result", {}).get("error_type", "")
    ).lower()
    if "not wired yet" in error or "runtimeerror" in error_type:
        return "hardware_bridge_failure"
    if skill_result.status != "success" and action_packet.next_skill in {"observe", "inspection"}:
        return "perception_failure"
    if skill_result.status != "success" and action_packet.next_skill in {"navigate_to", "fly_to"}:
        return "planning_failure"
    if skill_result.status != "success":
        return "skill_execution_failure"
    return None
