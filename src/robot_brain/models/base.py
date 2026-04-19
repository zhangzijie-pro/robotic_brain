from __future__ import annotations

from typing import Protocol

from robot_brain.core import ModelRequest, ModelResponse


class ModelClient(Protocol):
    """Common interface for local, cloud, and custom LLM/VLM providers."""

    provider: str

    async def infer(self, request: ModelRequest) -> ModelResponse:
        ...
