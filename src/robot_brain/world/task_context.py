from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskContext:
    task_id: str | None = None
    user_command: str | None = None
    goal: str | None = None
    status: str = "idle"
    active_step: str | None = None
    metadata: dict = field(default_factory=dict)

    def start(self, task_id: str, user_command: str, goal: str | None = None) -> None:
        self.task_id = task_id
        self.user_command = user_command
        self.goal = goal
        self.status = "running"

    def mark_failed(self, reason: str) -> None:
        self.status = "failed"
        self.metadata["failure_reason"] = reason

    def mark_succeeded(self) -> None:
        self.status = "succeeded"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "user_command": self.user_command,
            "goal": self.goal,
            "status": self.status,
            "active_step": self.active_step,
            "metadata": self.metadata,
        }
