from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import SkillResult


@dataclass
class ExecutionFeedbackBus:
    results: list[SkillResult] = field(default_factory=list)

    def publish(self, result: SkillResult) -> None:
        self.results.append(result)

    def latest(self, limit: int = 20) -> list[SkillResult]:
        return self.results[-limit:]
