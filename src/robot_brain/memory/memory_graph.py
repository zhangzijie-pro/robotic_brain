from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import LearningRecord
from robot_brain.learning.trajectory_schema import TaskTrajectory


@dataclass
class MemoryGraph:
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)

    def ingest_trajectory(
        self,
        trajectory: TaskTrajectory,
        records: list[LearningRecord],
    ) -> None:
        task_node = f"task:{trajectory.task_id}"
        self.nodes[task_node] = {
            "type": "TaskEpisode",
            "command": trajectory.command,
            "outcome": trajectory.outcome,
            "robot_type": trajectory.robot_type,
        }

        for step in trajectory.steps:
            skill_node = f"skill:{step.skill}"
            self.nodes.setdefault(skill_node, {"type": "Skill", "name": step.skill})
            self.edges.append(
                {"source": task_node, "target": skill_node, "relation": "used_skill"}
            )

        for record in records:
            if not record.root_cause:
                continue
            failure_node = f"failure:{record.root_cause}"
            self.nodes.setdefault(
                failure_node,
                {"type": "FailurePattern", "name": record.root_cause},
            )
            self.edges.append(
                {"source": task_node, "target": failure_node, "relation": "failed_under"}
            )

    def to_dict(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}
