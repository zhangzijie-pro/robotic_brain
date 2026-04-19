from __future__ import annotations

from robot_brain.core import Fact


class SafetyReviewAgent:
    name = "safety_review_agent"

    async def think(self, context: dict) -> list[Fact]:
        return [
            Fact(
                type="safety_review",
                subject="current_task",
                predicate="reviewed",
                object={"concerns": [], "requires_confirmation": False},
                confidence=0.0,
                source=self.name,
            )
        ]
