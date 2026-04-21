from __future__ import annotations


class RecoverySelector:
    def select(self, skill: str, risk_level: str, nearby_human: bool) -> str | None:
        if nearby_human or risk_level == "high":
            return "ask_human"
        if skill in {"grasp", "estimate_grasp_pose"}:
            return "observe"
        if skill in {"navigate_to", "fly_to"}:
            return "inspection"
        return None
