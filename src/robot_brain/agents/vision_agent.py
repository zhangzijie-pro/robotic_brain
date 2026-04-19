from __future__ import annotations

import os

from robot_brain.agents.base import Agent
from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact, VLMRequest
from robot_brain.vlm_service import VLMService


class VisionAgent(Agent):
    def __init__(self, vlm: VLMService, image_refs: list[str] | None = None) -> None:
        super().__init__(name="vision_agent", priority=70)
        self.vlm = vlm
        self.image_refs = image_refs or []

    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        prompt = """
You are the visual perception module of a robot.
Return only JSON. Use this schema:
{
  "objects": [
    {
      "id": "stable_object_id",
      "name": "short object name",
      "bbox": [x1, y1, x2, y2],
      "state": "short state",
      "location_hint": "short spatial hint",
      "confidence": 0.0
    }
  ],
  "scene_summary": "one sentence",
  "risks": ["short risk"],
  "uncertainty": ["short uncertainty"],
  "confidence": 0.0
}
If no image is provided, this is a dry-run demo: assume a red cup and a book
are on a table, and still return valid JSON.
"""
        response = await self.vlm.infer(
            VLMRequest(
                caller=self.name,
                prompt=prompt.strip(),
                image_refs=self.image_refs,
                priority=self.priority,
                deadline_ms=int(os.getenv("ROBOT_BRAIN_VLM_DEADLINE_MS", "8000")),
                schema={"required": ["objects", "scene_summary", "risks"]},
            )
        )

        facts: list[Fact] = [
            Fact(
                type="scene_summary",
                subject="scene",
                predicate="described_as",
                object=response.result.get("scene_summary", ""),
                confidence=response.confidence,
                source=self.name,
            )
        ]

        for item in response.result.get("objects", []):
            object_id = str(item.get("id") or item.get("name") or "unknown_object")
            facts.append(
                Fact(
                    type="object",
                    subject=object_id,
                    predicate="observed",
                    object=item,
                    confidence=float(item.get("confidence", response.confidence)),
                    source=self.name,
                )
            )

        for risk in response.result.get("risks", []):
            facts.append(
                Fact(
                    type="risk",
                    subject="scene",
                    predicate="has_risk",
                    object=risk,
                    confidence=response.confidence,
                    source=self.name,
                )
            )

        return facts
