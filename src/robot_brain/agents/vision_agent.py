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
        if self.image_refs:
            prompt = """
Return only JSON with keys: objects, scene_summary, risks, uncertainty, confidence.
Each object must include: id, name, bbox, state, location_hint, confidence.
Keep the response short and do not explain.
"""
            deadline_ms = int(os.getenv("ROBOT_BRAIN_VLM_IMAGE_DEADLINE_MS", "180000"))
        else:
            prompt = """
Return compact JSON only.
Scene: a red cup and a closed book are on a table.
Required keys: objects, scene_summary, risks, confidence.
objects must have exactly 2 items.
Each object must have id, name, location_hint, confidence.
Keep output short.
"""
            deadline_ms = int(os.getenv("ROBOT_BRAIN_VLM_DEADLINE_MS", "90000"))
        response = await self.vlm.infer(
            VLMRequest(
                caller=self.name,
                prompt=prompt.strip(),
                image_refs=self.image_refs,
                priority=self.priority,
                deadline_ms=deadline_ms,
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
