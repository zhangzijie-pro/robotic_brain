from __future__ import annotations

from robot_brain.core import LearningRecord
from robot_brain.feedback.failure_taxonomy import classify_trajectory_failure
from robot_brain.learning.lesson_extractor import extract_lesson
from robot_brain.learning.trajectory_schema import TaskTrajectory


class ReflectionEngine:
    def reflect(self, trajectory: TaskTrajectory) -> list[LearningRecord]:
        root_cause = classify_trajectory_failure(trajectory)
        lesson = extract_lesson(root_cause, trajectory)
        records: list[LearningRecord] = []

        for step in trajectory.steps:
            candidate_patch = None
            if root_cause and root_cause != "safety_rejection":
                candidate_patch = {
                    "target_skill": step.skill,
                    "patch_type": "skill_heuristic_update",
                    "proposed_variant": _suggest_variant(step.skill, root_cause),
                }

            records.append(
                LearningRecord(
                    task_id=trajectory.task_id,
                    selected_skill=step.skill,
                    world_state_features={
                        "robot_type": trajectory.robot_type,
                        "scene_summary": trajectory.final_world_state.get("scene_summary"),
                        "risk_count": len(trajectory.final_world_state.get("risks", [])),
                    },
                    safety_events=[step.safety_decision],
                    outcome=step.status,
                    root_cause=root_cause if step.status in {"failed", "blocked"} else None,
                    lesson=lesson,
                    candidate_patch=candidate_patch,
                    decision_trace=step.action_packet.get("decision_trace", {}),
                    reusable=step.status == "success" and trajectory.outcome == "success",
                    timestamps=trajectory.timestamps,
                )
            )

        return records


def _suggest_variant(skill: str, root_cause: str) -> str:
    if root_cause == "perception_failure":
        return f"{skill}_with_reobserve"
    if root_cause == "world_model_stale":
        return f"{skill}_after_scene_refresh"
    if root_cause == "hardware_bridge_failure":
        return f"{skill}_dry_run_fallback"
    if root_cause == "safety_rejection":
        return "ask_human"
    return f"{skill}_guarded"
