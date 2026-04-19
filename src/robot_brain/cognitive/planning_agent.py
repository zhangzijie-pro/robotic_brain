from __future__ import annotations

from robot_brain.brain import TaskPlanner
from robot_brain.brain.world_model import WorldModel
from robot_brain.core import Fact


class PlanningAgent:
    name = "planning_agent"

    async def think(self, context: dict) -> list[Fact]:
        world = context.get("world")
        if not isinstance(world, WorldModel):
            return []
        plan = TaskPlanner().create_plan(world)
        return [
            Fact(
                type="task_plan",
                subject="current_task",
                predicate="planned_as",
                object=[step.to_dict() for step in plan],
                confidence=0.8,
                source=self.name,
            )
        ]
