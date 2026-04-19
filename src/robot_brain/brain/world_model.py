from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.blackboard import Blackboard


@dataclass
class WorldModel:
    objects: dict[str, dict] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    robot_state: dict = field(default_factory=dict)
    human_state: dict = field(default_factory=dict)
    task_command: str | None = None
    scene_summary: str | None = None

    async def update_from_blackboard(self, blackboard: Blackboard) -> None:
        self.objects = {}
        self.risks = []
        self.robot_state = {}
        self.human_state = {}
        self.task_command = None
        self.scene_summary = None

        for fact in await blackboard.latest(limit=200):
            if fact.type == "object" and isinstance(fact.object, dict):
                self.objects[fact.subject] = {
                    **fact.object,
                    "confidence": fact.confidence,
                    "source": fact.source,
                }
            elif fact.type == "risk":
                self.risks.append(str(fact.object))
            elif fact.type == "robot_state" and isinstance(fact.object, dict):
                self.robot_state = fact.object
            elif fact.type == "human_state" and isinstance(fact.object, dict):
                self.human_state = fact.object
            elif fact.type == "task_command":
                self.task_command = str(fact.object)
            elif fact.type == "scene_summary":
                self.scene_summary = str(fact.object)

    def find_target_object(self) -> tuple[str, dict] | None:
        command = (self.task_command or "").lower()
        for object_id, payload in self.objects.items():
            name = str(payload.get("name", "")).lower()
            if "cup" in command and "cup" in name:
                return object_id, payload
            if "杯" in command and ("cup" in name or "杯" in name):
                return object_id, payload
        return next(iter(self.objects.items()), None)

    def to_dict(self) -> dict:
        return {
            "task_command": self.task_command,
            "scene_summary": self.scene_summary,
            "objects": self.objects,
            "risks": self.risks,
            "robot_state": self.robot_state,
            "human_state": self.human_state,
        }
