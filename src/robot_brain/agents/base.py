from __future__ import annotations

from abc import ABC, abstractmethod

from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact


class Agent(ABC):
    def __init__(self, name: str, priority: int = 50) -> None:
        self.name = name
        self.priority = priority

    @abstractmethod
    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        ...

    async def publish_once(self, blackboard: Blackboard) -> list[Fact]:
        facts = await self.run_once(blackboard)
        await blackboard.publish(facts)
        return facts

