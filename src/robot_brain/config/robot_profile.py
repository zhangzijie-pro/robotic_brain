from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robot_brain.core import RobotCapability, RobotProfile


def create_default_robot_profile(robot_type: str = "generic_mobile_manipulator") -> RobotProfile:
    if robot_type in {"drone", "generic_drone", "uav"}:
        return _create_default_drone_profile()

    capabilities = {
        "observe": RobotCapability(name="observe"),
        "navigate_to": RobotCapability(
            name="navigate_to",
            limits={"max_speed_mps": 0.25, "requires_localization": True},
        ),
        "estimate_grasp_pose": RobotCapability(name="estimate_grasp_pose"),
        "grasp": RobotCapability(
            name="grasp",
            limits={"max_arm_speed_scale": 0.2, "force_limited": True},
        ),
        "handover_to_human": RobotCapability(
            name="handover_to_human",
            limits={"min_human_distance_m": 0.8, "requires_confirmation": True},
        ),
        "follow_escort": RobotCapability(name="follow_escort", enabled=False),
        "inspection": RobotCapability(name="inspection", enabled=True),
        "dock_charge": RobotCapability(name="dock_charge", enabled=False),
        "fly_to": RobotCapability(name="fly_to", enabled=False),
    }
    return RobotProfile(
        robot_id="generic_robot",
        robot_type=robot_type,
        capabilities=capabilities,
        sensors={
            "rgb_camera": {"modality": "rgb", "frame_id": "camera_color_optical_frame"},
            "depth_camera": {"modality": "depth", "frame_id": "camera_depth_optical_frame"},
            "microphone": {"modality": "audio", "frame_id": "mic_array"},
            "imu": {"modality": "imu", "frame_id": "imu_link"},
        },
        control={
            "middleware": "dry_run",
            "namespace": "",
            "base_controller": "/cmd_vel",
            "arm_controller": "/follow_joint_trajectory",
            "gripper_controller": "/gripper_controller/gripper_cmd",
            "tts": "/tts",
        },
    )


def _create_default_drone_profile() -> RobotProfile:
    return RobotProfile(
        robot_id="generic_drone",
        robot_type="drone",
        base_frame="base_link",
        map_frame="map",
        capabilities={
            "observe": RobotCapability(name="observe"),
            "fly_to": RobotCapability(
                name="fly_to",
                limits={"max_speed_mps": 1.0, "max_altitude_m": 20.0},
            ),
            "inspection": RobotCapability(name="inspection"),
            "dock_charge": RobotCapability(name="dock_charge"),
            "navigate_to": RobotCapability(name="navigate_to", enabled=False),
            "grasp": RobotCapability(name="grasp", enabled=False),
            "handover_to_human": RobotCapability(
                name="handover_to_human",
                enabled=False,
            ),
        },
        sensors={
            "rgb_camera": {"modality": "rgb", "frame_id": "camera_color_optical_frame"},
            "depth_camera": {"modality": "depth", "frame_id": "camera_depth_optical_frame"},
            "imu": {"modality": "imu", "frame_id": "imu_link"},
            "lidar": {"modality": "lidar_radar", "frame_id": "lidar"},
        },
        control={
            "middleware": "dry_run",
            "namespace": "drone",
            "flight_controller": "/drone/fly_to_pose",
            "tts": "/drone/tts",
        },
    )


def robot_profile_from_dict(data: dict[str, Any]) -> RobotProfile:
    raw_capabilities = data.get("capabilities", {})
    capabilities = {
        name: RobotCapability(
            name=name,
            enabled=bool(payload.get("enabled", True)),
            interface=str(payload.get("interface", "dry_run")),
            limits=dict(payload.get("limits", {})),
            metadata=dict(payload.get("metadata", {})),
        )
        for name, payload in raw_capabilities.items()
        if isinstance(payload, dict)
    }
    return RobotProfile(
        robot_id=str(data.get("robot_id", "generic_robot")),
        robot_type=str(data.get("robot_type", "generic")),
        base_frame=str(data.get("base_frame", "base_link")),
        map_frame=str(data.get("map_frame", "map")),
        capabilities=capabilities,
        sensors=dict(data.get("sensors", {})),
        control=dict(data.get("control", {})),
    )


def load_robot_profile(path: str | Path | None = None) -> RobotProfile:
    if path is None:
        return create_default_robot_profile()

    profile_path = Path(path).expanduser()
    text = profile_path.read_text(encoding="utf-8")
    if profile_path.suffix.lower() == ".json":
        return robot_profile_from_dict(json.loads(text))

    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "YAML robot profiles require PyYAML. Use JSON or install PyYAML."
        ) from exc

    loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Robot profile must be a mapping: {profile_path}")
    return robot_profile_from_dict(loaded)
