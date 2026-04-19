from __future__ import annotations

from robot_brain.skills.base import Skill
from robot_brain.skills.docking_charging import DockingChargingSkill
from robot_brain.skills.follow_escort import FollowEscortSkill
from robot_brain.skills.human_interaction import HumanInteractionSkill
from robot_brain.skills.inspection import InspectionSkill, ObserveSkill
from robot_brain.skills.manipulation import EstimateGraspPoseSkill, GraspSkill
from robot_brain.skills.navigation import DroneFlyToSkill, NavigationSkill


class SkillRegistry:
    def __init__(self, skills: list[Skill] | None = None) -> None:
        self._skills: dict[str, Skill] = {}
        for skill in skills or default_skills():
            self.register(skill)

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise ValueError(f"Unsupported skill: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._skills)


def default_skills() -> list[Skill]:
    return [
        ObserveSkill(),
        NavigationSkill(),
        DroneFlyToSkill(),
        EstimateGraspPoseSkill(),
        GraspSkill(),
        HumanInteractionSkill(),
        FollowEscortSkill(),
        InspectionSkill(),
        DockingChargingSkill(),
    ]
