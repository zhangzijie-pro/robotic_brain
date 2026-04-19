from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import now_ts


@dataclass
class EpisodicMemory:
    episodes: list[dict] = field(default_factory=list)

    def record(self, event_type: str, payload: dict) -> None:
        self.episodes.append(
            {"event_type": event_type, "payload": payload, "timestamp": now_ts()}
        )

    def latest(self, limit: int = 20) -> list[dict]:
        return self.episodes[-limit:]
