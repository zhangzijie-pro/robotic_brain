from __future__ import annotations


class ModeManager:
    valid_modes = {"idle", "teleop", "assistive", "autonomous", "emergency_stop"}

    def __init__(self, initial_mode: str = "idle") -> None:
        self.mode = initial_mode

    def set_mode(self, mode: str) -> None:
        if mode not in self.valid_modes:
            raise ValueError(f"Unsupported robot mode: {mode}")
        self.mode = mode

    def allows_autonomy(self) -> bool:
        return self.mode in {"assistive", "autonomous"}
