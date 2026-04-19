from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UserProfileMemory:
    users: dict[str, dict] = field(default_factory=dict)

    def update_preference(self, user_id: str, key: str, value: object) -> None:
        profile = self.users.setdefault(user_id, {"preferences": {}})
        profile.setdefault("preferences", {})[key] = value

    def get_profile(self, user_id: str) -> dict:
        return self.users.get(user_id, {})
