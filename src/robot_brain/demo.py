from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
from robot_brain.core.messages import new_id
from robot_brain.decision_models import ParallelActionHead
from robot_brain.executive import PlannerBias
from robot_brain.feedback.failure_taxonomy import classify_step_failure
from robot_brain.learning.reflection_engine import ReflectionEngine
from robot_brain.learning.skill_distiller import SkillDistiller
from robot_brain.learning.strategy_optimizer import StrategyOptimizer
from robot_brain.learning.trajectory_recorder import TrajectoryRecorder
from robot_brain.memory import (
    EpisodicStore,
    MemoryGraph,
    MemoryRetriever,
    ProceduralStore,
    SpatialStore,
)
from robot_brain.skills import SkillExecutor
from robot_brain.vlm_service import VLMService, create_vlm_client


async def run_demo(
    command: str,
    image_refs: list[str],
    provider: str | None,
    robot_bridge: str | None = None,
    robot_type: str = "generic_mobile_manipulator",
) -> dict:
    task_id = new_id("task")
    blackboard = Blackboard()
    vlm = VLMService(create_vlm_client(provider=provider), max_concurrency=1)
    robot_profile = create_default_robot_profile(robot_type=robot_type)
    episodic_store_path = os.getenv("ROBOT_BRAIN_EPISODIC_STORE")
    episodic_store = EpisodicStore(
        path=Path(episodic_store_path).expanduser() if episodic_store_path else None
    )
    procedural_store = ProceduralStore()
    spatial_store = SpatialStore()
    memory_retriever = MemoryRetriever(
        episodic_store=episodic_store,
        procedural_store=procedural_store,
        spatial_store=spatial_store,
    )
    memory_graph = MemoryGraph()
    strategy_optimizer = StrategyOptimizer()

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
    for object_id, payload in world.objects.items():
        location_hint = str(payload.get("location_hint", "unknown"))
        spatial_store.remember_zone(
            location_hint,
            {"last_object_id": object_id, "scene_summary": world.scene_summary},
        )

    retrieved_cases = memory_retriever.retrieve_cases(
        task_text=command,
        robot_type=robot_type,
        scene_summary=world.scene_summary,
        top_k=5,
    )

    planner_bias = PlannerBias()
    plan = TaskPlanner().create_plan(
        world,
        robot_profile=robot_profile,
        retrieved_cases=retrieved_cases,
        planner_bias=planner_bias,
    )
    selected_steps = BehaviorPlanner().select_next_steps(plan)
    action_packets = ParallelActionHead().build_packets(
        task_id=task_id,
        plan=selected_steps,
        world=world,
        retrieved_cases=retrieved_cases,
    )
    safety = SafetySupervisor()
    executor = SkillExecutor(robot_bridge=create_robot_bridge(robot_bridge))
    recorder = TrajectoryRecorder(
        task_id=task_id,
        command=command,
        robot_type=robot_type,
        initial_world_state=world.to_dict(),
        retrieved_case_ids=[
            str(case.get("task_id"))
            for case in retrieved_cases
            if case.get("task_id")
        ],
    )

    execution_trace = []
    for step, action_packet in zip(selected_steps, action_packets):
        decision = safety.check(step, world)
        trace_item = {
            "step": step.to_dict(),
            "action_packet": action_packet.to_dict(),
            "safety": decision.to_dict(),
            "skill_result": None,
        }
        result = None
        if decision.allowed:
            result = await executor.execute(step)
            await blackboard.publish(result.to_fact())
            trace_item["skill_result"] = {
                "skill": result.skill,
                "status": result.status,
                "details": result.details,
                "latency_ms": result.latency_ms,
            }
            procedural_store.record_outcome(step.skill, success=result.status == "success")
        else:
            procedural_store.record_outcome(step.skill, success=False)

        recorder.record_step(
            action_packet=action_packet,
            safety_decision=decision,
            skill_result=result,
            failure_type=classify_step_failure(action_packet, decision, result),
        )
        execution_trace.append(trace_item)
        if not decision.allowed:
            break
        if (
            trace_item["skill_result"]
            and trace_item["skill_result"]["status"] != "success"
        ):
            break

    await world.update_from_blackboard(blackboard)
    trajectory = recorder.finalize(world.to_dict())
    episodic_store.add_trajectory(trajectory)
    learning_records = ReflectionEngine().reflect(trajectory)
    strategy_optimizer.update(learning_records)

    skill_distiller = SkillDistiller()
    skill_patches = []
    for record in learning_records:
        patch = skill_distiller.distill(record)
        if patch:
            procedural_store.record_patch(patch)
            skill_patches.append(patch.to_dict())

    memory_graph.ingest_trajectory(trajectory, learning_records)
    return {
        "task_id": task_id,
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
        "action_packets": [packet.to_dict() for packet in action_packets],
        "planner_context": {
            "retrieved_cases": [_summarize_case(case) for case in retrieved_cases],
            "planner_bias_applied": bool(
                plan and plan[0].name == "observe_scene_refresh"
            ),
        },
        "execution_trace": execution_trace,
        "trajectory": trajectory.to_dict(),
        "learning_records": [record.to_dict() for record in learning_records],
        "skill_patches": skill_patches,
        "strategy_snapshot": strategy_optimizer.snapshot(),
        "procedural_memory": procedural_store.snapshot(),
        "memory_graph": memory_graph.to_dict(),
        "blackboard": await blackboard.snapshot(),
    }


def _summarize_case(case: dict) -> dict:
    failed_steps = [
        step.get("skill")
        for step in case.get("steps", [])
        if step.get("status") in {"blocked", "failed"}
    ]
    return {
        "task_id": case.get("task_id"),
        "command": case.get("command"),
        "outcome": case.get("outcome"),
        "failed_steps": failed_steps,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local robot brain demo.")
    parser.add_argument(
        "--task",
        default="把桌上的红杯子拿给我",
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
