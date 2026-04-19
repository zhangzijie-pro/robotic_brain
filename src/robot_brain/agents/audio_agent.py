from __future__ import annotations

from robot_brain.agents.base import Agent
from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact


class AudioAgent(Agent):
    def __init__(self, command_text: str) -> None:
        super().__init__(name="audio_agent", priority=50)
        self.command_text = command_text

    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        return [
            Fact(
                type="task_command",
                subject="user",
                predicate="requested",
                object=self.command_text,
                confidence=0.98,
                source=self.name,
            )
        ]

