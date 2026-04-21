from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpatialStore:
    zones: dict[str, dict] = field(default_factory=dict)

    def remember_zone(self, zone_id: str, payload: dict) -> None:
        self.zones[zone_id] = {**self.zones.get(zone_id, {}), **payload}

    def get_zone(self, zone_id: str) -> dict | None:
        return self.zones.get(zone_id)
