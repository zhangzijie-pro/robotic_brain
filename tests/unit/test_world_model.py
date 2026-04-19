import asyncio
import unittest

from robot_brain.blackboard import Blackboard
from robot_brain.brain import WorldModel
from robot_brain.core import Fact


class WorldModelTest(unittest.TestCase):
    def test_world_model_finds_cup_from_chinese_command(self):
        async def scenario():
            blackboard = Blackboard()
            await blackboard.publish(
                [
                    Fact(
                        type="task_command",
                        subject="user",
                        predicate="requested",
                        object="把桌上的红杯子拿给我",
                        confidence=1.0,
                        source="test",
                    ),
                    Fact(
                        type="object",
                        subject="red_cup_001",
                        predicate="observed",
                        object={"name": "red cup"},
                        confidence=0.9,
                        source="test",
                    ),
                ]
            )
            world = WorldModel()
            await world.update_from_blackboard(blackboard)
            return world.find_target_object()

        target = asyncio.run(scenario())
        self.assertIsNotNone(target)
        self.assertEqual(target[0], "red_cup_001")


if __name__ == "__main__":
    unittest.main()
