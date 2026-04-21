from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from robot_brain.learning.trajectory_schema import TaskTrajectory


@dataclass
class EpisodicStore:
    path: Path | None = None
    trajectories: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.path and self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                self.trajectories = [
                    json.loads(line)
                    for line in handle
                    if line.strip()
                ]

    def add_trajectory(self, trajectory: TaskTrajectory) -> None:
        payload = trajectory.to_dict()
        self.trajectories.append(payload)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 20) -> list[dict]:
        return self.trajectories[-limit:]
