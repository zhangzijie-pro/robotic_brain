from __future__ import annotations

from robot_brain.core import PlanStep


class PlannerBias:
    def apply(self, plan: list[PlanStep], retrieved_cases: list[dict]) -> list[PlanStep]:
        if not retrieved_cases:
            return plan

        failure_roots = {
            step.get("failure_type")
            for case in retrieved_cases
            for step in case.get("steps", [])
            if step.get("status") in {"blocked", "failed"}
        }
        if "perception_failure" in failure_roots and (
            not plan or plan[0].skill != "observe"
        ):
            return [
                PlanStep(
                    name="observe_scene_refresh",
                    skill="observe",
                    args={"reason": "planner_bias_from_retrieved_failures"},
                    risk="low",
                ),
                *plan,
            ]
        return plan
