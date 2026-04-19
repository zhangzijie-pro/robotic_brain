from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import SensorFrame


@dataclass(slots=True)
class TemplateSensor:
    sensor_id: str
    modality: str
    frame_id: str | None = None
    metadata: dict = field(default_factory=dict)

    async def read_once(self) -> SensorFrame:
        return SensorFrame(
            sensor_id=self.sensor_id,
            modality=self.modality,
            frame_id=self.frame_id,
            payload={
                "status": "not_connected",
                "metadata": self.metadata,
                "note": "replace TemplateSensor.read_once with your driver binding",
            },
        )


class RGBCameraSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "rgb_camera", frame_id: str = "camera_color_optical_frame") -> None:
        super().__init__(sensor_id=sensor_id, modality="rgb", frame_id=frame_id)


class DepthCameraSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "depth_camera", frame_id: str = "camera_depth_optical_frame") -> None:
        super().__init__(sensor_id=sensor_id, modality="depth", frame_id=frame_id)


class LidarRadarSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "lidar_radar", frame_id: str = "laser") -> None:
        super().__init__(sensor_id=sensor_id, modality="lidar_radar", frame_id=frame_id)


class AudioIOSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "mic_array", frame_id: str = "mic_array") -> None:
        super().__init__(sensor_id=sensor_id, modality="audio", frame_id=frame_id)


class ImuEncoderSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "imu_encoder", frame_id: str = "base_link") -> None:
        super().__init__(sensor_id=sensor_id, modality="proprioception", frame_id=frame_id)


class ForceSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "force_sensor", frame_id: str = "wrist_force_torque") -> None:
        super().__init__(sensor_id=sensor_id, modality="force", frame_id=frame_id)


class TactileSensor(TemplateSensor):
    def __init__(self, sensor_id: str = "tactile_sensor", frame_id: str = "gripper") -> None:
        super().__init__(sensor_id=sensor_id, modality="tactile", frame_id=frame_id)
