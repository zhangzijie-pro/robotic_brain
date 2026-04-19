from __future__ import annotations

from robot_brain.agents.base import Agent
from robot_brain.blackboard import Blackboard
from robot_brain.core import Fact


class SpatialAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="spatial_agent", priority=75)

    async def run_once(self, blackboard: Blackboard) -> list[Fact]:
        object_facts = await blackboard.by_type("object")
        facts: list[Fact] = []

        for fact in object_facts:
            object_payload = fact.object if isinstance(fact.object, dict) else {}
            object_name = str(object_payload.get("name", fact.subject))
            location_hint = str(object_payload.get("location_hint", "unknown"))
            facts.append(
                Fact(
                    type="spatial_relation",
                    subject=fact.subject,
                    predicate="located_at",
                    object={
                        "frame": "map",
                        "location_hint": location_hint,
                        "estimated_xyz_m": [0.7, 0.0, 0.78],
                    },
                    confidence=min(fact.confidence, 0.75),
                    source=self.name,
                )
            )
            facts.append(
                Fact(
                    type="reachability",
                    subject=fact.subject,
                    predicate="is_reachable",
                    object={
                        "reachable": "cup" in object_name.lower()
                        or location_hint == "on_table",
                        "reason": "demo tabletop reachability estimate",
                    },
                    confidence=0.7,
                    source=self.name,
                )
            )

        return facts

