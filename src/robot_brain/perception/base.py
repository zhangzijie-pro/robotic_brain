from __future__ import annotations

from typing import Protocol

from robot_brain.core import PerceptionResult, SensorFrame


class PerceptionNode(Protocol):
    """Consumes sensor frames and emits structured perception results."""

    name: str

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        ...
