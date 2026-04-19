from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from uuid import uuid4


def now_ts() -> float:
    return time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


@dataclass(slots=True)
class Observation:
    source: str
    data: dict
    timestamp: float = field(default_factory=now_ts)
    frame_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SensorFrame:
    sensor_id: str
    modality: str
    payload: dict
    timestamp: float = field(default_factory=now_ts)
    frame_id: str | None = None
    sequence_id: str = field(default_factory=lambda: new_id("frame"))

    def to_observation(self, source: str | None = None) -> Observation:
        return Observation(
            source=source or self.sensor_id,
            data={
                "sensor_id": self.sensor_id,
                "modality": self.modality,
                **self.payload,
            },
            timestamp=self.timestamp,
            frame_id=self.frame_id,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PerceptionResult:
    node: str
    result_type: str
    data: dict
    confidence: float
    timestamp: float = field(default_factory=now_ts)
    frame_id: str | None = None

    def to_fact(self, subject: str, predicate: str = "perceived") -> Fact:
        return Fact(
            type=self.result_type,
            subject=subject,
            predicate=predicate,
            object=self.data,
            confidence=self.confidence,
            source=self.node,
            timestamp=self.timestamp,
            frame_id=self.frame_id,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class VLMRequest:
    caller: str
    prompt: str
    image_refs: list[str] = field(default_factory=list)
    schema: dict = field(default_factory=dict)
    priority: int = 50
    deadline_ms: int = 8000
    request_id: str = field(default_factory=lambda: new_id("vlm_req"))


@dataclass(slots=True)
class VLMResponse:
    request_id: str
    result: dict
    confidence: float
    latency_ms: int
    model_version: str
    evidence_refs: list[str] = field(default_factory=list)
    raw_text: str | None = None


@dataclass(slots=True)
class ModelRequest:
    caller: str
    prompt: str
    modality: str = "text"
    image_refs: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    schema: dict = field(default_factory=dict)
    priority: int = 50
    deadline_ms: int = 8000
    request_id: str = field(default_factory=lambda: new_id("model_req"))


@dataclass(slots=True)
class ModelResponse:
    request_id: str
    result: dict | str
    confidence: float
    latency_ms: int
    provider: str
    model_version: str
    raw_text: str | None = None
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Fact:
    type: str
    subject: str
    predicate: str
    object: str | dict | list | float | int | bool | None
    confidence: float
    source: str
    timestamp: float = field(default_factory=now_ts)
    frame_id: str | None = None
    expires_after_ms: int | None = None
    fact_id: str = field(default_factory=lambda: new_id("fact"))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PlanStep:
    name: str
    skill: str
    args: dict = field(default_factory=dict)
    risk: str = "low"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SafetyDecision:
    allowed: bool
    reason: str
    required_confirmation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SkillResult:
    skill: str
    status: str
    details: dict = field(default_factory=dict)
    latency_ms: int = 0

    def to_fact(self, source: str = "skill_executor") -> Fact:
        return Fact(
            type="skill_result",
            subject=self.skill,
            predicate="completed_with_status",
            object={"status": self.status, **self.details},
            confidence=1.0,
            source=source,
        )


@dataclass(slots=True)
class RobotCapability:
    name: str
    enabled: bool = True
    interface: str = "dry_run"
    limits: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RobotProfile:
    robot_id: str
    robot_type: str
    base_frame: str = "base_link"
    map_frame: str = "map"
    capabilities: dict[str, RobotCapability] = field(default_factory=dict)
    sensors: dict[str, dict] = field(default_factory=dict)
    control: dict = field(default_factory=dict)

    def has_capability(self, name: str) -> bool:
        capability = self.capabilities.get(name)
        return bool(capability and capability.enabled)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "capabilities": {
                name: capability.to_dict()
                for name, capability in self.capabilities.items()
            },
        }
