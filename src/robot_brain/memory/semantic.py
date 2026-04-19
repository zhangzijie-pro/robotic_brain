from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SemanticMemory:
    facts: dict[str, dict] = field(default_factory=dict)

    def upsert(self, key: str, value: dict) -> None:
        self.facts[key] = {**self.facts.get(key, {}), **value}

    def get(self, key: str) -> dict | None:
        return self.facts.get(key)
