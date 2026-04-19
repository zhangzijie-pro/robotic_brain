from __future__ import annotations

import asyncio
import time

from robot_brain.control import RobotBridge, create_robot_bridge
from robot_brain.core import PlanStep, SkillResult
from robot_brain.skills.registry import SkillRegistry


class SkillExecutor:
    def __init__(
        self,
        robot_bridge: RobotBridge | None = None,
        skill_registry: SkillRegistry | None = None,
    ) -> None:
        self.robot_bridge = robot_bridge or create_robot_bridge()
        self.skill_registry = skill_registry or SkillRegistry()

    async def execute(self, step: PlanStep) -> SkillResult:
        start = time.perf_counter()
        status = "success"
        try:
            command_result = await self._dispatch(step)
        except Exception as exc:
            status = "failed"
            command_result = {"error": str(exc), "error_type": type(exc).__name__}

        await asyncio.sleep(0)
        details = {
            "step": step.name,
            "args": step.args,
            "robot_bridge": self.robot_bridge.name,
            "command_result": command_result,
        }
        latency_ms = int((time.perf_counter() - start) * 1000)
        return SkillResult(
            skill=step.skill,
            status=status,
            details=details,
            latency_ms=latency_ms,
        )

    async def _dispatch(self, step: PlanStep) -> dict:
        skill = self.skill_registry.get(step.skill)
        return await skill.run(step, self.robot_bridge)
