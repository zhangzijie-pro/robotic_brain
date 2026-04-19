import asyncio
import unittest

from robot_brain.demo import run_demo


class DemoTest(unittest.TestCase):
    def test_demo_stops_after_failed_skill_execution(self):
        output = asyncio.run(
            run_demo(
                command="把桌上的红杯子拿给我",
                image_refs=[],
                provider="mock",
                robot_bridge="ros2",
            )
        )

        self.assertEqual(len(output["execution_trace"]), 1)
        self.assertEqual(
            output["execution_trace"][0]["skill_result"]["status"], "failed"
        )


if __name__ == "__main__":
    unittest.main()
