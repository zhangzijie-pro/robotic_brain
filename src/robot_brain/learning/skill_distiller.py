from __future__ import annotations

from robot_brain.core import LearningRecord, SkillPatch


class SkillDistiller:
    def distill(self, record: LearningRecord) -> SkillPatch | None:
        candidate = record.candidate_patch or {}
        target_skill = str(candidate.get("target_skill") or record.selected_skill)
        if not target_skill:
            return None

        patch_fields: dict[str, object] = {}
        proposed_variant = candidate.get("proposed_variant")
        if proposed_variant:
            patch_fields["preferred_variant"] = proposed_variant

        if record.root_cause == "safety_rejection":
            patch_fields["fallback_order"] = ["ask_human", target_skill]
        elif record.root_cause == "perception_failure":
            patch_fields["switch_rules"] = [
                "if target confidence drops, run multi_view_reobserve before retry"
            ]
        elif record.reusable:
            patch_fields["routing_bias"] = "prefer_in_similar_scene"

        if not patch_fields:
            return None

        return SkillPatch(
            target_skill=target_skill,
            patch_type=str(candidate.get("patch_type") or "skill_heuristic_update"),
            fields=patch_fields,
            rationale=record.lesson,
            status="draft",
            confidence=0.75 if record.reusable else 0.6,
        )
