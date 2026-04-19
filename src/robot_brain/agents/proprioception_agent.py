from __future__ import annotations

from robot_brain.agents.base import Agent
from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact


class ProprioceptionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="proprioception_agent", priority=80)

    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        return [
            Fact(
                type="robot_state",
                subject="robot",
                predicate="has_state",
                object={
                    "mode": "local_demo",
                    "battery": 0.82,
                    "base_stopped": True,
                    "arm_ready": True,
                    "emergency_stop": False,
                },
                confidence=1.0,
                source=self.name,
            )
        ]

