from __future__ import annotations

from robot_brain.core import PerceptionResult, SensorFrame


class SafetyMonitorNode:
    """Template for emergency stop, collision, human distance, and fault checks."""

    name = "safety_monitor_node"

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        if not frames:
            return []
        return [
            PerceptionResult(
                node=self.name,
                result_type="safety_state",
                data={
                    "hard_stop": False,
                    "human_too_close": False,
                    "collision_predicted": False,
                    "faults": [],
                    "status": "template",
                },
                confidence=0.0,
                frame_id=frames[0].frame_id,
            )
        ]
