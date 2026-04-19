from __future__ import annotations

from robot_brain.core import Fact


class TaskParsingAgent:
    name = "task_parsing_agent"

    async def think(self, context: dict) -> list[Fact]:
        command = str(context.get("command", ""))
        return [
            Fact(
                type="task_intent",
                subject="user",
                predicate="intends",
                object={"raw_command": command, "intent": "unknown"},
                confidence=0.0,
                source=self.name,
            )
        ]
