from __future__ import annotations

from robot_brain.feedback.failure_logs import FailureLog
from robot_brain.memory import EpisodicMemory


class MemoryUpdatePipeline:
    def __init__(self, episodic_memory: EpisodicMemory | None = None) -> None:
        self.episodic_memory = episodic_memory or EpisodicMemory()

    def ingest_failures(self, failure_log: FailureLog) -> None:
        for entry in failure_log.entries:
            self.episodic_memory.record("skill_failure", entry)
