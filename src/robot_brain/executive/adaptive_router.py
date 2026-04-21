from __future__ import annotations

from robot_brain.executive.recovery_selector import RecoverySelector


class AdaptiveRouter:
    def __init__(self, recovery_selector: RecoverySelector | None = None) -> None:
        self.recovery_selector = recovery_selector or RecoverySelector()

    def suggest_fallback(
        self,
        skill: str,
        risk_level: str,
        nearby_human: bool,
    ) -> str | None:
        return self.recovery_selector.select(skill, risk_level, nearby_human)
