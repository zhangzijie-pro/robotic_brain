from __future__ import annotations

from robot_brain.config import create_default_robot_profile
from robot_brain.core import Fact, PlanStep, RobotProfile


class SkillRoutingAgent:
    name = "skill_routing_agent"

    async def think(self, context: dict) -> list[Fact]:
        profile = context.get("robot_profile") or create_default_robot_profile()
        steps = context.get("plan", [])
        if not isinstance(profile, RobotProfile):
            return []
        routable = [
            step.to_dict()
            for step in steps
            if isinstance(step, PlanStep) and profile.has_capability(step.skill)
        ]
        return [
            Fact(
                type="skill_route",
                subject="current_task",
                predicate="routable_steps",
                object=routable,
                confidence=1.0,
                source=self.name,
            )
        ]
