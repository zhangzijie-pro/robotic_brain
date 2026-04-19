from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from robot_brain.core import ModelRequest, ModelResponse
from robot_brain.models.base import ModelClient
from robot_brain.vlm_service.providers import _parse_jsonish


def create_model_client(provider: str | None = None) -> ModelClient:
    provider = provider or os.getenv("ROBOT_BRAIN_MODEL_PROVIDER", "mock")
    provider = provider.lower().strip().replace("-", "_")
    if provider == "mock":
        return MockModelClient()
    if provider == "ollama":
        return OllamaModelClient(
            base_url=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"),
            model=os.getenv("ROBOT_BRAIN_OLLAMA_MODEL", "qwen3-vl:2b"),
        )
    if provider in {"openai_compatible", "cloud", "custom_http"}:
        return OpenAICompatibleModelClient(
            base_url=os.getenv("ROBOT_BRAIN_MODEL_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("ROBOT_BRAIN_MODEL_API_KEY", ""),
            model=os.getenv("ROBOT_BRAIN_MODEL_NAME", "gpt-4.1-mini"),
            provider=provider,
        )
    raise ValueError(f"Unsupported model provider: {provider}")


class ModelGateway:
    def __init__(self, client: ModelClient, max_concurrency: int = 2) -> None:
        self._client = client
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def infer(self, request: ModelRequest) -> ModelResponse:
        async with self._semaphore:
            return await self._client.infer(request)


class MockModelClient:
    provider = "mock"

    async def infer(self, request: ModelRequest) -> ModelResponse:
        start = time.perf_counter()
        result: dict | str
        if request.modality == "vision":
            result = {
                "objects": [],
                "scene_summary": "mock model response",
                "risks": [],
                "confidence": 0.5,
            }
        else:
            result = "mock model response"
        return ModelResponse(
            request_id=request.request_id,
            result=result,
            confidence=0.5,
            latency_ms=int((time.perf_counter() - start) * 1000),
            provider=self.provider,
            model_version="mock-model",
            raw_text=json.dumps(result, ensure_ascii=False)
            if isinstance(result, dict)
            else result,
            evidence_refs=request.image_refs,
        )


class OllamaModelClient:
    provider = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def infer(self, request: ModelRequest) -> ModelResponse:
        start = time.perf_counter()
        payload = {
            "model": self.model,
            "stream": False,
            "messages": request.messages
            or [
                {
                    "role": "user",
                    "content": request.prompt,
                    "images": [_image_to_base64(path) for path in request.image_refs],
                }
            ],
        }
        data = _post_json(f"{self.base_url}/api/chat", payload, {}, request.deadline_ms)
        raw_text = data.get("message", {}).get("content", "")
        result: dict | str = _parse_jsonish(raw_text) if request.schema else raw_text
        return ModelResponse(
            request_id=request.request_id,
            result=result,
            confidence=float(result.get("confidence", 0.65))
            if isinstance(result, dict)
            else 0.65,
            latency_ms=int((time.perf_counter() - start) * 1000),
            provider=self.provider,
            model_version=f"ollama:{self.model}",
            raw_text=raw_text,
            evidence_refs=request.image_refs,
        )


class OpenAICompatibleModelClient:
    """Cloud or self-hosted endpoint using the /v1/chat/completions shape."""

    def __init__(self, base_url: str, api_key: str, model: str, provider: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = provider

    async def infer(self, request: ModelRequest) -> ModelResponse:
        start = time.perf_counter()
        messages = request.messages or [_to_openai_user_message(request)]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": float(os.getenv("ROBOT_BRAIN_MODEL_TEMPERATURE", "0.1")),
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post_json(
            f"{self.base_url}/chat/completions",
            payload,
            headers,
            request.deadline_ms,
        )
        raw_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        result: dict | str = _parse_jsonish(raw_text) if request.schema else raw_text
        return ModelResponse(
            request_id=request.request_id,
            result=result,
            confidence=float(result.get("confidence", 0.65))
            if isinstance(result, dict)
            else 0.65,
            latency_ms=int((time.perf_counter() - start) * 1000),
            provider=self.provider,
            model_version=f"{self.provider}:{self.model}",
            raw_text=raw_text,
            evidence_refs=request.image_refs,
        )


def _post_json(url: str, payload: dict, headers: dict, deadline_ms: int) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=deadline_ms / 1000) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach model provider at {url}") from exc


def _image_to_base64(path: str) -> str:
    image_path = Path(path).expanduser()
    with image_path.open("rb") as file:
        return base64.b64encode(file.read()).decode("ascii")


def _to_openai_user_message(request: ModelRequest) -> dict:
    if not request.image_refs:
        return {"role": "user", "content": request.prompt}
    content: list[dict] = [{"type": "text", "text": request.prompt}]
    for path in request.image_refs:
        encoded = _image_to_base64(path)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
            }
        )
    return {"role": "user", "content": content}
