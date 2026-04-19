from __future__ import annotations

from robot_brain.core import Fact


class ReflectionLearningAgent:
    name = "reflection_learning_agent"

    async def think(self, context: dict) -> list[Fact]:
        failures = context.get("failures", [])
        if not failures:
            return []
        return [
            Fact(
                type="learning_suggestion",
                subject="current_task",
                predicate="suggested_update",
                object={
                    "failures": failures,
                    "suggestions": [],
                    "apply_automatically": False,
                },
                confidence=0.0,
                source=self.name,
            )
        ]
