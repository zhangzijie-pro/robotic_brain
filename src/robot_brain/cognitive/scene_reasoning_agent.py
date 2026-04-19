from __future__ import annotations

from robot_brain.core import Fact


class SceneReasoningAgent:
    name = "scene_reasoning_agent"

    async def think(self, context: dict) -> list[Fact]:
        return [
            Fact(
                type="scene_reasoning",
                subject="scene",
                predicate="requires_reasoning",
                object={"relations": [], "unknowns": [], "status": "template"},
                confidence=0.0,
                source=self.name,
            )
        ]
