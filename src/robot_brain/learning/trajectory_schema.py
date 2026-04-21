from __future__ import annotations

from dataclasses import asdict, dataclass, field

from robot_brain.core.messages import now_ts


@dataclass(slots=True)
class TrajectoryStepRecord:
    step_name: str
    skill: str
    action_packet: dict
    safety_decision: dict
    skill_result: dict | None = None
    failure_type: str | None = None
    status: str = "pending"
    timestamp: float = field(default_factory=now_ts)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class TaskTrajectory:
    task_id: str
    command: str
    robot_type: str
    initial_world_state: dict
    final_world_state: dict = field(default_factory=dict)
    retrieved_case_ids: list[str] = field(default_factory=list)
    steps: list[TrajectoryStepRecord] = field(default_factory=list)
    outcome: str = "unknown"
    reward: float = 0.0
    timestamps: dict = field(default_factory=lambda: {"started_at": now_ts()})

    def add_step(self, record: TrajectoryStepRecord) -> None:
        self.steps.append(record)

    def finish(self, final_world_state: dict) -> None:
        self.final_world_state = final_world_state
        self.timestamps["finished_at"] = now_ts()
        if any(step.status in {"blocked", "failed"} for step in self.steps):
            self.outcome = "failed"
        else:
            self.outcome = "success"
        self.reward = sum(1.0 for step in self.steps if step.status == "success")
        self.reward -= sum(
            1.0 for step in self.steps if step.status in {"blocked", "failed"}
        )

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload
