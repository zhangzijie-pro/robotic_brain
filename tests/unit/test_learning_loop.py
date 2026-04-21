import asyncio
import unittest

from robot_brain.demo import run_demo


class LearningLoopTest(unittest.TestCase):
    def test_demo_emits_action_packets_and_learning_records(self):
        output = asyncio.run(
            run_demo(
                command="把桌上的红杯子拿给我",
                image_refs=[],
                provider="mock",
                robot_bridge="dry_run",
            )
        )

        self.assertEqual(len(output["action_packets"]), len(output["plan"]))
        self.assertEqual(output["trajectory"]["outcome"], "success")
        self.assertTrue(output["learning_records"])
        self.assertIn("strategy_snapshot", output)
        self.assertIn("memory_graph", output)
        self.assertTrue(
            all(packet["task_id"] == output["task_id"] for packet in output["action_packets"])
        )

    def test_failed_ros2_run_is_reflected_as_hardware_bridge_failure(self):
        output = asyncio.run(
            run_demo(
                command="把桌上的红杯子拿给我",
                image_refs=[],
                provider="mock",
                robot_bridge="ros2",
            )
        )

        failed_records = [
            record
            for record in output["learning_records"]
            if record["outcome"] in {"failed", "blocked"}
        ]
        self.assertTrue(failed_records)
        self.assertEqual(failed_records[0]["root_cause"], "hardware_bridge_failure")


if __name__ == "__main__":
    unittest.main()
