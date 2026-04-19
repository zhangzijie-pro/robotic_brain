from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import SkillResult, now_ts


@dataclass
class FailureLog:
    entries: list[dict] = field(default_factory=list)

    def record(self, result: SkillResult) -> None:
        if result.status == "success":
            return
        self.entries.append(
            {
                "skill": result.skill,
                "status": result.status,
                "details": result.details,
                "timestamp": now_ts(),
            }
        )
