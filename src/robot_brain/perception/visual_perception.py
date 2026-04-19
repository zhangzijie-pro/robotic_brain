from __future__ import annotations

from robot_brain.core import PerceptionResult, SensorFrame


class VisualPerceptionNode:
    """Template for detection, tracking, pose estimation, and scene semantics."""

    name = "visual_perception_node"

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        image_frames = [frame for frame in frames if frame.modality in {"rgb", "depth"}]
        if not image_frames:
            return []
        return [
            PerceptionResult(
                node=self.name,
                result_type="visual_perception",
                data={
                    "detections": [],
                    "tracks": [],
                    "poses": [],
                    "scene_semantics": {},
                    "status": "template",
                },
                confidence=0.0,
                frame_id=image_frames[0].frame_id,
            )
        ]
