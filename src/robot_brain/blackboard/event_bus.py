from __future__ import annotations

import asyncio
from collections import defaultdict

from robot_brain.core import Fact


class Blackboard:
    """Small in-memory blackboard for local prototyping."""

    def __init__(self) -> None:
        self._facts: list[Fact] = []
        self._by_type: dict[str, list[Fact]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, facts: Fact | list[Fact]) -> None:
        if isinstance(facts, Fact):
            facts = [facts]
        async with self._lock:
            for fact in facts:
                self._facts.append(fact)
                self._by_type[fact.type].append(fact)

    async def latest(self, limit: int = 20) -> list[Fact]:
        async with self._lock:
            return list(self._facts[-limit:])

    async def by_type(self, fact_type: str) -> list[Fact]:
        async with self._lock:
            return list(self._by_type.get(fact_type, []))

    async def snapshot(self) -> dict:
        async with self._lock:
            return {
                "fact_count": len(self._facts),
                "types": {key: len(value) for key, value in self._by_type.items()},
                "latest": [fact.to_dict() for fact in self._facts[-20:]],
            }

