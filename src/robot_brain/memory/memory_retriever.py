from __future__ import annotations

from robot_brain.memory.episodic_store import EpisodicStore
from robot_brain.memory.procedural_store import ProceduralStore
from robot_brain.memory.spatial_store import SpatialStore


class MemoryRetriever:
    def __init__(
        self,
        episodic_store: EpisodicStore,
        procedural_store: ProceduralStore,
        spatial_store: SpatialStore,
    ) -> None:
        self.episodic_store = episodic_store
        self.procedural_store = procedural_store
        self.spatial_store = spatial_store

    def retrieve_cases(
        self,
        task_text: str,
        robot_type: str,
        scene_summary: str | None,
        top_k: int = 5,
    ) -> list[dict]:
        task_text = task_text.lower()
        scene_summary = (scene_summary or "").lower()
        scored: list[tuple[int, dict]] = []
        for item in self.episodic_store.recent(limit=50):
            score = 0
            command = str(item.get("command", "")).lower()
            if any(token and token in command for token in task_text.split()):
                score += 2
            if item.get("robot_type") == robot_type:
                score += 2
            if scene_summary and scene_summary == str(
                item.get("final_world_state", {}).get("scene_summary", "")
            ).lower():
                score += 1
            if score:
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:top_k]]
