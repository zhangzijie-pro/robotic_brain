from __future__ import annotations

from typing import Protocol

from robot_brain.core import Fact


class CognitiveAgent(Protocol):
    name: str

    async def think(self, context: dict) -> list[Fact]:
        ...
