from __future__ import annotations

import os
from typing import Protocol


class RobotBridge(Protocol):
    """Hardware-facing adapter used by skills.

    The brain should decide *what* skill to run. The bridge decides *how* that
    skill reaches the robot middleware or device driver.
    """

    name: str

    async def observe(self, args: dict) -> dict:
        ...

    async def navigate_to(self, location_hint: str, args: dict) -> dict:
        ...

    async def estimate_grasp_pose(self, object_id: str, args: dict) -> dict:
        ...

    async def grasp(self, object_id: str, args: dict) -> dict:
        ...

    async def handover_to_human(self, recipient: str, args: dict) -> dict:
        ...

    async def follow_escort(self, target: str, args: dict) -> dict:
        ...

    async def inspect(self, target: str, args: dict) -> dict:
        ...

    async def dock_charge(self, station_id: str, args: dict) -> dict:
        ...

    async def fly_to(self, pose: dict, args: dict) -> dict:
        ...


def create_robot_bridge(provider: str | None = None) -> RobotBridge:
    provider = provider or os.getenv("ROBOT_BRAIN_ROBOT_BRIDGE", "dry_run")
    provider = provider.lower().strip().replace("-", "_")
    if provider in {"dry_run", "mock"}:
        return DryRunRobotBridge()
    if provider == "ros2":
        return Ros2RobotBridge()
    raise ValueError(f"Unsupported robot bridge: {provider}")


class DryRunRobotBridge:
    """Safe local bridge that records intended hardware actions."""

    name = "dry_run"

    async def observe(self, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "sensor snapshot + perception refresh",
            "args": args,
        }

    async def navigate_to(self, location_hint: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "Nav2 NavigateToPose",
            "target": {"location_hint": location_hint},
            "args": args,
        }

    async def estimate_grasp_pose(self, object_id: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "MoveIt grasp pose estimation pipeline",
            "target": {"object_id": object_id},
            "grasp_pose_hint": {
                "frame": "base_link",
                "xyz_m": [0.55, 0.0, 0.82],
                "approach_axis": "top_down",
            },
            "args": args,
        }

    async def grasp(self, object_id: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "MoveIt pick action + gripper close",
            "target": {"object_id": object_id},
            "args": args,
        }

    async def handover_to_human(self, recipient: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "arm handover pose + force-limited gripper release",
            "target": {"recipient": recipient},
            "args": args,
        }

    async def follow_escort(self, target: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "person tracking + velocity controller",
            "target": {"target": target},
            "args": args,
        }

    async def inspect(self, target: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "inspection route + sensor capture",
            "target": {"target": target},
            "args": args,
        }

    async def dock_charge(self, station_id: str, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "dock alignment + charging protocol",
            "target": {"station_id": station_id},
            "args": args,
        }

    async def fly_to(self, pose: dict, args: dict) -> dict:
        return {
            "sent_to_hardware": False,
            "would_call": "drone waypoint action",
            "target": {"pose": pose},
            "args": args,
        }


class Ros2RobotBridge:
    """ROS2 adapter placeholder for a real robot deployment.

    This class intentionally does not publish fake ROS commands. Fill these
    methods with your robot's action clients, services, and topic publishers
    after validating the safety limits in simulation.
    """

    name = "ros2"

    def __init__(self) -> None:
        self._namespace = os.getenv("ROBOT_BRAIN_ROS_NAMESPACE", "").strip("/")

    async def observe(self, args: dict) -> dict:
        return self._not_wired(
            "observe",
            {
                "topics_to_read": [
                    self._topic("camera/color/image_raw"),
                    self._topic("camera/depth/image_raw"),
                    self._topic("joint_states"),
                    self._topic("tf"),
                ],
                "args": args,
            },
        )

    async def navigate_to(self, location_hint: str, args: dict) -> dict:
        return self._not_wired(
            "navigate_to",
            {
                "action": self._topic("navigate_to_pose"),
                "target": {"location_hint": location_hint},
                "args": args,
            },
        )

    async def estimate_grasp_pose(self, object_id: str, args: dict) -> dict:
        return self._not_wired(
            "estimate_grasp_pose",
            {
                "pipeline": "perception object pose -> MoveIt planning scene",
                "target": {"object_id": object_id},
                "args": args,
            },
        )

    async def grasp(self, object_id: str, args: dict) -> dict:
        return self._not_wired(
            "grasp",
            {
                "action": self._topic("move_group"),
                "target": {"object_id": object_id},
                "args": args,
            },
        )

    async def handover_to_human(self, recipient: str, args: dict) -> dict:
        return self._not_wired(
            "handover_to_human",
            {
                "actions": [
                    self._topic("move_group"),
                    self._topic("gripper_controller/gripper_cmd"),
                ],
                "target": {"recipient": recipient},
                "args": args,
            },
        )

    async def follow_escort(self, target: str, args: dict) -> dict:
        return self._not_wired(
            "follow_escort",
            {
                "topics": [self._topic("cmd_vel"), self._topic("tracked_person")],
                "target": {"target": target},
                "args": args,
            },
        )

    async def inspect(self, target: str, args: dict) -> dict:
        return self._not_wired(
            "inspect",
            {
                "actions": [
                    self._topic("navigate_to_pose"),
                    self._topic("sensor_capture"),
                ],
                "target": {"target": target},
                "args": args,
            },
        )

    async def dock_charge(self, station_id: str, args: dict) -> dict:
        return self._not_wired(
            "dock_charge",
            {
                "action": self._topic("dock"),
                "target": {"station_id": station_id},
                "args": args,
            },
        )

    async def fly_to(self, pose: dict, args: dict) -> dict:
        return self._not_wired(
            "fly_to",
            {
                "action": self._topic("fly_to_pose"),
                "target": {"pose": pose},
                "args": args,
            },
        )

    def _topic(self, name: str) -> str:
        if not self._namespace:
            return f"/{name}"
        return f"/{self._namespace}/{name}"

    def _not_wired(self, skill: str, command: dict) -> dict:
        raise RuntimeError(
            "ROS2 robot bridge is selected but not wired yet. "
            f"Implement Ros2RobotBridge.{skill}() with your robot middleware. "
            f"Prepared command envelope: {command}"
        )
