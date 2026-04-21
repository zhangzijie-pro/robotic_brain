from __future__ import annotations

from dataclasses import dataclass, field

from robot_brain.core import SkillPatch


@dataclass
class ProceduralStore:
    patches_by_skill: dict[str, list[dict]] = field(default_factory=dict)
    outcomes_by_skill: dict[str, dict] = field(default_factory=dict)

    def record_patch(self, patch: SkillPatch) -> None:
        self.patches_by_skill.setdefault(patch.target_skill, []).append(patch.to_dict())

    def record_outcome(self, skill: str, success: bool) -> None:
        stats = self.outcomes_by_skill.setdefault(
            skill,
            {"success_count": 0, "failure_count": 0},
        )
        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

    def snapshot(self) -> dict:
        return {
            "patches_by_skill": self.patches_by_skill,
            "outcomes_by_skill": self.outcomes_by_skill,
        }
