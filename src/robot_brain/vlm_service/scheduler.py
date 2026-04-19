from __future__ import annotations

import asyncio

from robot_brain.core import VLMRequest, VLMResponse
from robot_brain.vlm_service.providers import VLMClient


class VLMService:
    """Shared VLM gateway.

    This first version serializes access through a semaphore. It gives every
    Agent a single stable interface while leaving room for batching later.
    """

    def __init__(self, client: VLMClient, max_concurrency: int = 1) -> None:
        self._client = client
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def infer(self, request: VLMRequest) -> VLMResponse:
        async with self._semaphore:
            return await self._client.infer(request)

