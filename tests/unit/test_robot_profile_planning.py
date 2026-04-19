import asyncio
import unittest

from robot_brain.blackboard import Blackboard
from robot_brain.brain import TaskPlanner, WorldModel
from robot_brain.config import create_default_robot_profile
from robot_brain.core import Fact
from robot_brain.demo import run_demo


class RobotProfilePlanningTest(unittest.TestCase):
    def test_drone_profile_uses_fly_to_and_inspection_instead_of_grasp(self):
        async def scenario():
            blackboard = Blackboard()
            await blackboard.publish(
                [
                    Fact(
                        type="task_command",
                        subject="user",
                        predicate="requested",
                        object="检查桌上的红杯子",
                        confidence=1.0,
                        source="test",
                    ),
                    Fact(
                        type="object",
                        subject="red_cup_001",
                        predicate="observed",
                        object={"name": "red cup", "location_hint": "on_table"},
                        confidence=0.9,
                        source="test",
                    ),
                ]
            )
            world = WorldModel()
            await world.update_from_blackboard(blackboard)
            return TaskPlanner().create_plan(
                world,
                robot_profile=create_default_robot_profile("drone"),
            )

        plan = asyncio.run(scenario())
        self.assertEqual([step.skill for step in plan], ["observe", "fly_to", "inspection"])

    def test_demo_accepts_drone_profile(self):
        output = asyncio.run(
            run_demo(
                command="检查桌上的红杯子",
                image_refs=[],
                provider="mock",
                robot_bridge="dry_run",
                robot_type="drone",
            )
        )

        self.assertEqual(output["robot_profile"]["robot_type"], "drone")
        self.assertEqual(
            [step["skill"] for step in output["plan"]],
            ["observe", "fly_to", "inspection"],
        )


if __name__ == "__main__":
    unittest.main()
