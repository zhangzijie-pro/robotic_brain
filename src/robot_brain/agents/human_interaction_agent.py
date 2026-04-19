from __future__ import annotations

from robot_brain.agents.base import Agent
from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact


class HumanInteractionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="human_interaction_agent", priority=65)

    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        return [
            Fact(
                type="human_state",
                subject="user",
                predicate="is_available_for_handover",
                object={
                    "available": True,
                    "distance_m": 1.2,
                    "hand_visible": True,
                },
                confidence=0.72,
                source=self.name,
            )
        ]

