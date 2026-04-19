from __future__ import annotations

from typing import Protocol

from robot_brain.control import RobotBridge
from robot_brain.core import PlanStep


class Skill(Protocol):
    """Standard skill template for robot-independent high-level actions."""

    name: str
    default_risk: str

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        ...
