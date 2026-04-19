from __future__ import annotations

from robot_brain.core import PerceptionResult, SensorFrame


class RobotStateEstimator:
    """Template for IMU, encoder, joint, battery, and actuator state fusion."""

    name = "robot_state_estimator"

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        state_frames = [
            frame
            for frame in frames
            if frame.modality in {"proprioception", "imu", "force", "tactile"}
        ]
        if not state_frames:
            return []
        return [
            PerceptionResult(
                node=self.name,
                result_type="robot_state",
                data={
                    "mode": "unknown",
                    "base_stopped": True,
                    "arm_ready": False,
                    "battery": None,
                    "emergency_stop": None,
                    "status": "template",
                },
                confidence=0.0,
                frame_id=state_frames[0].frame_id,
            )
        ]
