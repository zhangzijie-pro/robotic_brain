from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol

from robot_brain.core import VLMRequest, VLMResponse


class VLMClient(Protocol):
    async def infer(self, request: VLMRequest) -> VLMResponse:
        ...


def create_vlm_client(provider: str | None = None) -> VLMClient:
    provider = provider or os.getenv("ROBOT_BRAIN_VLM_PROVIDER", "mock")
    provider = provider.lower().strip()
    if provider == "mock":
        return MockVLMClient()
    if provider == "ollama":
        return OllamaVLMClient(
            base_url=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"),
            model=os.getenv("ROBOT_BRAIN_OLLAMA_MODEL", "qwen2.5:3b"),
        )
    raise ValueError(f"Unsupported VLM provider: {provider}")


class MockVLMClient:
    async def infer(self, request: VLMRequest) -> VLMResponse:
        start = time.perf_counter()
        result = {
            "objects": [
                {
                    "id": "red_cup_001",
                    "name": "red cup",
                    "bbox": [120, 80, 210, 190],
                    "state": "upright",
                    "location_hint": "on_table",
                    "confidence": 0.86,
                },
                {
                    "id": "book_001",
                    "name": "book",
                    "bbox": [260, 95, 420, 180],
                    "state": "closed",
                    "location_hint": "on_table",
                    "confidence": 0.74,
                },
            ],
            "scene_summary": "A red cup is on a table near a closed book.",
            "risks": ["red cup is close to table edge"],
            "uncertainty": ["handle direction is unclear"],
        }
        latency_ms = int((time.perf_counter() - start) * 1000)
        return VLMResponse(
            request_id=request.request_id,
            result=result,
            confidence=0.82,
            latency_ms=latency_ms,
            model_version="mock-vlm",
            evidence_refs=request.image_refs,
            raw_text=json.dumps(result, ensure_ascii=False),
        )


class OllamaVLMClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def infer(self, request: VLMRequest) -> VLMResponse:
        start = time.perf_counter()
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt,
                    "images": [_image_to_base64(path) for path in request.image_refs],
                }
            ],
            "options": {
                "temperature": float(os.getenv("ROBOT_BRAIN_VLM_TEMPERATURE", "0.1"))
            },
        }

        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                http_request, timeout=request.deadline_ms / 1000
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise RuntimeError(
                "Timed out while waiting for Ollama /api/chat. "
                f"host={self.base_url}, model={self.model}, "
                f"timeout_ms={request.deadline_ms}. "
                "Local models can be slow on the first request; try increasing "
                "ROBOT_BRAIN_VLM_DEADLINE_MS, for example 30000."
            ) from exc
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                "Ollama returned an HTTP error while running /api/chat. "
                f"host={self.base_url}, model={self.model}, "
                f"status={exc.code}, body={error_body!r}. "
                "If this is 404, the model is usually missing or the model name "
                "does not match `ollama list`. Run `ollama pull <model>` or set "
                "ROBOT_BRAIN_OLLAMA_MODEL to an installed vision-capable model."
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise RuntimeError(
                    "Timed out while waiting for Ollama /api/chat. "
                    f"host={self.base_url}, model={self.model}, "
                    f"timeout_ms={request.deadline_ms}. "
                    "Local models can be slow on the first request; try increasing "
                    "ROBOT_BRAIN_VLM_DEADLINE_MS, for example 30000."
                ) from exc
            raise RuntimeError(
                "Could not connect to Ollama while running /api/chat. "
                f"host={self.base_url}, model={self.model}, reason={exc.reason!r}. "
                "From Docker on macOS, run Ollama on the Mac host and use "
                "OLLAMA_HOST=http://host.docker.internal:11434."
            ) from exc

        raw_text = data.get("message", {}).get("content", "")
        result = _parse_jsonish(raw_text)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return VLMResponse(
            request_id=request.request_id,
            result=result,
            confidence=float(result.get("confidence", 0.65)),
            latency_ms=latency_ms,
            model_version=f"ollama:{self.model}",
            evidence_refs=request.image_refs,
            raw_text=raw_text,
        )


def _image_to_base64(path: str) -> str:
    image_path = Path(path).expanduser()
    with image_path.open("rb") as file:
        return base64.b64encode(file.read()).decode("ascii")


def _parse_jsonish(text: str) -> dict:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"items": parsed}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        except json.JSONDecodeError:
            pass

    return {
        "objects": [],
        "scene_summary": text.strip(),
        "risks": [],
        "uncertainty": ["provider returned non-json content"],
        "confidence": 0.4,
    }
