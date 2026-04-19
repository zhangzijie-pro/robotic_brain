from __future__ import annotations

from robot_brain.core import PerceptionResult, SensorFrame


class AudioNode:
    """Template for ASR, speaker verification, and sound source localization."""

    name = "audio_node"

    async def process(self, frames: list[SensorFrame]) -> list[PerceptionResult]:
        audio_frames = [frame for frame in frames if frame.modality == "audio"]
        if not audio_frames:
            return []
        return [
            PerceptionResult(
                node=self.name,
                result_type="audio_perception",
                data={
                    "transcript": "",
                    "speaker_id": None,
                    "source_direction": None,
                    "status": "template",
                },
                confidence=0.0,
                frame_id=audio_frames[0].frame_id,
            )
        ]
