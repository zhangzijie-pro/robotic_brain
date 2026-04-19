from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SceneGraph:
    """Lightweight entity-relation graph for objects, places, humans, and robots."""

    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)

    def upsert_node(self, node_id: str, node_type: str, attrs: dict | None = None) -> None:
        current = self.nodes.get(node_id, {})
        self.nodes[node_id] = {
            **current,
            "id": node_id,
            "type": node_type,
            **(attrs or {}),
        }

    def add_relation(
        self,
        source: str,
        relation: str,
        target: str,
        confidence: float = 1.0,
        attrs: dict | None = None,
    ) -> None:
        self.edges.append(
            {
                "source": source,
                "relation": relation,
                "target": target,
                "confidence": confidence,
                **(attrs or {}),
            }
        )

    def to_dict(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}
