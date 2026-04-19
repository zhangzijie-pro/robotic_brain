from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RewardSignalTracker:
    signals: list[dict] = field(default_factory=list)

    def record(self, task_id: str, value: float, reason: str) -> None:
        self.signals.append({"task_id": task_id, "value": value, "reason": reason})
