from __future__ import annotations

from typing import Protocol


class BaseController(Protocol):
    async def send_velocity(self, linear_mps: float, angular_radps: float) -> dict:
        ...


class ArmController(Protocol):
    async def execute_pose(self, pose: dict, speed_scale: float = 0.2) -> dict:
        ...


class GripperController(Protocol):
    async def command(self, width_m: float | None = None, force_n: float | None = None) -> dict:
        ...


class SpeechTTS(Protocol):
    async def say(self, text: str, voice: str | None = None) -> dict:
        ...


class DroneController(Protocol):
    async def fly_to(self, pose: dict, speed_mps: float) -> dict:
        ...


class Ros2Interface(Protocol):
    async def call_action(self, name: str, goal: dict, timeout_ms: int) -> dict:
        ...

    async def call_service(self, name: str, request: dict, timeout_ms: int) -> dict:
        ...

    async def publish_topic(self, name: str, message: dict) -> dict:
        ...
