from __future__ import annotations

from robot_brain.learning.trajectory_schema import TaskTrajectory


LESSON_TEMPLATES = {
    "perception_failure": "re-observe from another viewpoint before committing to manipulation",
    "grounding_failure": "add entity grounding checks before selecting the target skill",
    "world_model_stale": "refresh scene state before high-risk steps when evidence is stale",
    "planning_failure": "inject retrieved cases and planner bias before decomposing the task",
    "skill_execution_failure": "prefer a safer fallback variant when the primary skill fails",
    "safety_rejection": "route through a lower-risk fallback when humans are nearby",
    "human_ambiguity": "ask the operator for clarification before executing ambiguous goals",
    "environment_out_of_distribution": "switch to inspection-first behavior in unknown environments",
    "hardware_bridge_failure": "keep a dry-run or inspection fallback when robot wiring is incomplete",
}


def extract_lesson(root_cause: str | None, trajectory: TaskTrajectory) -> str | None:
    if not root_cause:
        if trajectory.outcome == "success" and trajectory.steps:
            return (
                f"{trajectory.steps[-1].skill} stayed stable for this task; "
                "prefer the same routing in similar conditions"
            )
        return None

    lesson = LESSON_TEMPLATES.get(root_cause)
    if not lesson:
        return None

    if not trajectory.steps:
        return lesson
    return f"After {trajectory.steps[-1].skill}, {lesson}"
