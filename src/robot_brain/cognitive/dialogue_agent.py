from __future__ import annotations

from robot_brain.core import Fact


class DialogueAgent:
    name = "dialogue_agent"

    async def think(self, context: dict) -> list[Fact]:
        prompt = context.get("prompt")
        if not prompt:
            return []
        return [
            Fact(
                type="dialogue_act",
                subject="robot",
                predicate="should_say",
                object={"text": "", "reason": "template response"},
                confidence=0.0,
                source=self.name,
            )
        ]
