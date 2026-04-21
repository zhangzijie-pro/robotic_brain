from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import LearningRecord


@dataclass
class SkillStrategyStats:
    success_count: int = 0
    failure_count: int = 0
    lessons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        total = self.success_count + self.failure_count
        success_rate = self.success_count / total if total else 0.0
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(success_rate, 3),
            "lessons": self.lessons[-3:],
        }


class StrategyOptimizer:
    def __init__(self) -> None:
        self._by_skill: dict[str, SkillStrategyStats] = {}

    def update(self, records: list[LearningRecord]) -> None:
        for record in records:
            stats = self._by_skill.setdefault(record.selected_skill, SkillStrategyStats())
            if record.outcome == "success":
                stats.success_count += 1
            elif record.outcome in {"failed", "blocked"}:
                stats.failure_count += 1
            if record.lesson:
                stats.lessons.append(record.lesson)

    def snapshot(self) -> dict:
        return {skill: stats.to_dict() for skill, stats in sorted(self._by_skill.items())}
