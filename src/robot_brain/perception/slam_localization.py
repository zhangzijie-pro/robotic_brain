from __future__ import annotations

from robot_brain.core import PerceptionResult, SensorFrame


class SlamLocalizationNode:
    """Template for SLAM, localization, and semantic map updates."""

    name = "slam_localization_node"

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        useful = [frame for frame in frames if frame.modality in {"lidar_radar", "rgb", "depth", "imu"}]
        if not useful:
            return []
        return [
            PerceptionResult(
                node=self.name,
                result_type="localization",
                data={
                    "pose": None,
                    "covariance": None,
                    "map_updates": [],
                    "status": "template",
                },
                confidence=0.0,
                frame_id=useful[0].frame_id,
            )
        ]
