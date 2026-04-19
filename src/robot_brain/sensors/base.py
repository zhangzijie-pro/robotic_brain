from __future__ import annotations

from typing import Protocol

from robot_brain.core import SensorFrame


class SensorAdapter(Protocol):
    """Standard adapter for any physical or simulated sensor."""

    sensor_id: str
    modality: str

    async def read_once(self) -> SensorFrame:
        ...
