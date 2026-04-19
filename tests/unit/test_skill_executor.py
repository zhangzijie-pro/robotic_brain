import asyncio
import unittest

from robot_brain.control import DryRunRobotBridge, Ros2RobotBridge
from robot_brain.core import PlanStep
from robot_brain.skills import SkillExecutor


class SkillExecutorTest(unittest.TestCase):
    def test_dry_run_bridge_records_intended_hardware_action(self):
        async def scenario():
            executor = SkillExecutor(robot_bridge=DryRunRobotBridge())
            return await executor.execute(
                PlanStep(
                    name="navigate_to_target_area",
                    skill="navigate_to",
                    args={"location_hint": "on_table"},
                    risk="medium",
                )
            )

        result = asyncio.run(scenario())

        self.assertEqual(result.status, "success")
        self.assertEqual(result.details["robot_bridge"], "dry_run")
        self.assertFalse(result.details["command_result"]["sent_to_hardware"])
        self.assertEqual(
            result.details["command_result"]["would_call"], "Nav2 NavigateToPose"
        )

    def test_ros2_bridge_fails_closed_until_robot_specific_wiring_exists(self):
        async def scenario():
            executor = SkillExecutor(robot_bridge=Ros2RobotBridge())
            return await executor.execute(
                PlanStep(
                    name="grasp_target",
                    skill="grasp",
                    args={"object_id": "red_cup_001"},
                    risk="high",
                )
            )

        result = asyncio.run(scenario())

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.details["robot_bridge"], "ros2")
        self.assertEqual(result.details["command_result"]["error_type"], "RuntimeError")
        self.assertIn("not wired yet", result.details["command_result"]["error"])


if __name__ == "__main__":
    unittest.main()
