from __future__ import annotations

from robot_brain.brain.world_model import WorldModel
from robot_brain.core import ActionPacket, DecisionTrace, PlanStep
from robot_brain.executive.adaptive_router import AdaptiveRouter


class ParallelActionHead:
    """Heuristic stand-in for a future multi-head structured output model."""

    def __init__(self, adaptive_router: AdaptiveRouter | None = None) -> None:
        self.adaptive_router = adaptive_router or AdaptiveRouter()

    def build_packets(
        self,
        task_id: str,
        plan: list[PlanStep],
        world: WorldModel,
        retrieved_cases: list[dict] | None = None,
    ) -> list[ActionPacket]:
        retrieved_cases = retrieved_cases or []
        packets: list[ActionPacket] = []
        nearby_human = float(world.human_state.get("distance_m", 99.0)) < 1.0

        for step in plan:
            target_id = _extract_target_id(step)
            fallback_skill = self.adaptive_router.suggest_fallback(
                step.skill,
                step.risk,
                nearby_human,
            )
            confidence = _estimate_confidence(step, world, target_id)
            packets.append(
                ActionPacket(
                    task_id=task_id,
                    intent=_intent_for_skill(step.skill),
                    target_id=target_id,
                    next_skill=step.skill,
                    skill_args=step.args,
                    risk_level=step.risk,
                    need_replan=step.skill == "observe" and not bool(world.objects),
                    need_human=fallback_skill == "ask_human",
                    fallback_skill=fallback_skill,
                    confidence=confidence,
                    decision_trace=DecisionTrace(
                        reason_codes=_reason_codes(step, world),
                        confidence_sources=_confidence_sources(world, target_id),
                        retrieved_case_ids=[
                            str(case.get("task_id"))
                            for case in retrieved_cases[:3]
                            if case.get("task_id")
                        ],
                        safety_rationale=(
                            "human_nearby_guard"
                            if nearby_human and step.risk == "high"
                            else "normal_safety_window"
                        ),
                    ),
                )
            )
        return packets


def _extract_target_id(step: PlanStep) -> str | None:
    for key in ("object_id", "target", "recipient"):
        value = step.args.get(key)
        if isinstance(value, str):
            return value
    return None


def _intent_for_skill(skill: str) -> str:
    if skill in {"navigate_to", "fly_to"}:
        return "move"
    if skill in {"grasp", "estimate_grasp_pose"}:
        return "manipulate"
    if skill in {"handover_to_human", "ask_human"}:
        return "handover"
    return "inspect"


def _estimate_confidence(step: PlanStep, world: WorldModel, target_id: str | None) -> float:
    if target_id and target_id in world.objects:
        base = float(world.objects[target_id].get("confidence", 0.6))
    else:
        base = 0.55 if world.objects else 0.4
    if step.risk == "high":
        base -= 0.1
    return round(max(0.1, min(base, 0.95)), 3)


def _reason_codes(step: PlanStep, world: WorldModel) -> list[str]:
    codes = [f"skill:{step.skill}", f"risk:{step.risk}"]
    if world.risks:
        codes.extend(f"scene_risk:{risk}" for risk in world.risks[:2])
    if world.human_state.get("available"):
        codes.append("human_available")
    return codes


def _confidence_sources(world: WorldModel, target_id: str | None) -> list[str]:
    sources = []
    if target_id and target_id in world.objects:
        sources.append(f"object_confidence:{target_id}")
    if world.scene_summary:
        sources.append("scene_summary")
    if world.robot_state:
        sources.append("robot_state")
    return sources
