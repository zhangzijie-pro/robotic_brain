from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from robot_brain.agents import (
    AudioAgent,
    HumanInteractionAgent,
    ProprioceptionAgent,
    SpatialAgent,
    VisionAgent,
)
from robot_brain.blackboard import Blackboard
from robot_brain.brain import (
    BehaviorPlanner,
    SafetySupervisor,
    TaskPlanner,
    WorldModel,
)
from robot_brain.config import create_default_robot_profile
from robot_brain.control import create_robot_bridge
from robot_brain.skills import SkillExecutor
from robot_brain.vlm_service import VLMService, create_vlm_client


async def run_demo(
    command: str,
    image_refs: list[str],
    provider: str | None,
    robot_bridge: str | None = None,
    robot_type: str = "generic_mobile_manipulator",
) -> dict:
    blackboard = Blackboard()
    vlm = VLMService(create_vlm_client(provider=provider), max_concurrency=1)
    robot_profile = create_default_robot_profile(robot_type=robot_type)

    initial_agents = [
        AudioAgent(command_text=command),
        VisionAgent(vlm=vlm, image_refs=image_refs),
        ProprioceptionAgent(),
        HumanInteractionAgent(),
    ]

    initial_results = await asyncio.gather(
        *(agent.publish_once(blackboard) for agent in initial_agents)
    )

    spatial_agent = SpatialAgent()
    spatial_results = await spatial_agent.publish_once(blackboard)

    world = WorldModel()
    await world.update_from_blackboard(blackboard)

    plan = TaskPlanner().create_plan(world, robot_profile=robot_profile)
    selected_steps = BehaviorPlanner().select_next_steps(plan)
    safety = SafetySupervisor()
    executor = SkillExecutor(robot_bridge=create_robot_bridge(robot_bridge))

    execution_trace = []
    for step in selected_steps:
        decision = safety.check(step, world)
        trace_item = {
            "step": step.to_dict(),
            "safety": decision.to_dict(),
            "skill_result": None,
        }
        if decision.allowed:
            result = await executor.execute(step)
            await blackboard.publish(result.to_fact())
            trace_item["skill_result"] = {
                "skill": result.skill,
                "status": result.status,
                "details": result.details,
                "latency_ms": result.latency_ms,
            }
        execution_trace.append(trace_item)
        if not decision.allowed:
            break
        if (
            trace_item["skill_result"]
            and trace_item["skill_result"]["status"] != "success"
        ):
            break

    await world.update_from_blackboard(blackboard)
    return {
        "provider": provider or os.getenv("ROBOT_BRAIN_VLM_PROVIDER", "mock"),
        "robot_bridge": robot_bridge
        or os.getenv("ROBOT_BRAIN_ROBOT_BRIDGE", "dry_run"),
        "robot_profile": robot_profile.to_dict(),
        "command": command,
        "image_refs": image_refs,
        "agent_fact_counts": {
            "initial": [len(items) for items in initial_results],
            "spatial": len(spatial_results),
        },
        "world_model": world.to_dict(),
        "plan": [step.to_dict() for step in plan],
        "execution_trace": execution_trace,
        "blackboard": await blackboard.snapshot(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local robot brain demo.")
    parser.add_argument(
        "--task",
        default="who am i ",
        help="Natural language task command.",
    )
    parser.add_argument(
        "--image",
        action="append",
        # default=["src/robot_brain/img.jpg"],
        default=[],
        help="Optional image path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "ollama"],
        default=os.getenv("ROBOT_BRAIN_VLM_PROVIDER", "mock"),
        help="VLM provider. Use mock first, then ollama when your local model is ready.",
    )
    parser.add_argument(
        "--robot-bridge",
        choices=["dry_run", "ros2"],
        default=os.getenv("ROBOT_BRAIN_ROBOT_BRIDGE", "dry_run"),
        help="Robot bridge. dry_run is safe; ros2 is a wiring skeleton for real robots.",
    )
    parser.add_argument(
        "--robot-type",
        default=os.getenv("ROBOT_BRAIN_ROBOT_TYPE", "generic_mobile_manipulator"),
        help="Robot profile type, e.g. generic_mobile_manipulator or drone.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    image_refs = []
    for image in args.image:
        path = Path(image).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        image_refs.append(str(path))

    try:
        output = asyncio.run(
            run_demo(
                command=args.task,
                image_refs=image_refs,
                provider=args.provider,
                robot_bridge=args.robot_bridge,
                robot_type=args.robot_type,
            )
        )
    except RuntimeError as exc:
        parser.exit(1, f"Error: {exc}\n")

    if args.pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
