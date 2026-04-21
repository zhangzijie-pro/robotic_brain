from __future__ import annotations

import base64
import asyncio
import http.client
import json
import os
import re
import time
import urllib.parse
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
            base_url=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
            model=os.getenv("ROBOT_BRAIN_OLLAMA_MODEL"),
            text_model=os.getenv("ROBOT_BRAIN_OLLAMA_TEXT_MODEL", "qwen3.5:0.8b"),
            vision_model=os.getenv("ROBOT_BRAIN_OLLAMA_VISION_MODEL", "qwen3-vl:2b"),
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
    def __init__(
        self,
        base_url: str,
        model: str | None,
        text_model: str,
        vision_model: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.text_model = text_model
        self.vision_model = vision_model

    async def infer(self, request: VLMRequest) -> VLMResponse:
        start = time.perf_counter()
        active_model = self._select_model(request)
        payload, endpoint = self._build_payload(request, active_model)

        max_attempts = int(os.getenv("ROBOT_BRAIN_OLLAMA_RETRIES", "2")) + 1
        for attempt in range(1, max_attempts + 1):
            try:
                data = _post_ollama_json(
                    f"{self.base_url}{endpoint}",
                    payload,
                    request.deadline_ms,
                )
                break
            except TimeoutError as exc:
                raise RuntimeError(
                    f"Timed out while waiting for Ollama {endpoint}. "
                    f"host={self.base_url}, model={active_model}, "
                    f"timeout_ms={request.deadline_ms}. "
                    "Local models can be slow on the first request; try increasing "
                    "ROBOT_BRAIN_VLM_DEADLINE_MS or ROBOT_BRAIN_VLM_IMAGE_DEADLINE_MS."
                ) from exc
            except OllamaHTTPError as exc:
                if exc.status in {502, 503, 504} and attempt < max_attempts:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                raise RuntimeError(
                    f"Ollama returned an HTTP error while running {endpoint}. "
                    f"host={self.base_url}, model={active_model}, "
                    f"status={exc.status}, body={exc.body!r}. "
                    "If this is 404, the model is usually missing or the model name "
                    "does not match `ollama list`. If this is 502/503/504, Ollama "
                    "is reachable but the local model runner failed or was busy; "
                    "retry, run `ollama ps`, or restart Ollama."
                ) from exc
            except OSError as exc:
                raise RuntimeError(
                    f"Could not connect to Ollama while running {endpoint}. "
                    f"host={self.base_url}, model={active_model}, reason={exc!r}. "
                    "From Docker on macOS, run Ollama on the Mac host and use "
                    "OLLAMA_HOST=http://host.docker.internal:11434."
                ) from exc

        raw_text = (
            data.get("message", {}).get("content", "")
            if request.image_refs
            else data.get("response", "")
        )
        result = _parse_jsonish(raw_text)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return VLMResponse(
            request_id=request.request_id,
            result=result,
            confidence=_as_float(result.get("confidence"), 0.65),
            latency_ms=latency_ms,
            model_version=f"ollama:{active_model}",
            evidence_refs=request.image_refs,
            raw_text=raw_text,
        )

    def _select_model(self, request: VLMRequest) -> str:
        if self.model:
            return self.model
        if request.image_refs:
            return self.vision_model
        return self.text_model

    def _build_payload(self, request: VLMRequest, active_model: str) -> tuple[dict, str]:
        temperature = float(os.getenv("ROBOT_BRAIN_VLM_TEMPERATURE", "0.1"))
        if request.image_refs:
            return (
                {
                    "model": active_model,
                    "stream": True,
                    "think": _ollama_think_value(),
                    "format": "json",
                    "messages": [
                        {
                            "role": "user",
                            "content": request.prompt,
                            "images": [_image_to_base64(path) for path in request.image_refs],
                        }
                    ],
                    "options": {"temperature": temperature},
                },
                "/api/chat",
            )

        return (
            {
                "model": active_model,
                "stream": False,
                "think": _ollama_think_value(),
                "format": "json",
                "prompt": request.prompt,
                "options": {
                    "temperature": temperature,
                    "num_predict": int(
                        os.getenv("ROBOT_BRAIN_OLLAMA_TEXT_NUM_PREDICT", "160")
                    ),
                },
            },
            "/api/generate",
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


class OllamaHTTPError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"Ollama HTTP {status}: {body}")
        self.status = status
        self.body = body


def _post_ollama_json(url: str, payload: dict, deadline_ms: int) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported Ollama URL scheme: {parsed.scheme}")

    body = json.dumps(payload).encode("utf-8")
    connection_cls = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    connection = connection_cls(
        parsed.hostname,
        parsed.port,
        timeout=deadline_ms / 1000,
    )
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )
        response = connection.getresponse()
        if payload.get("stream"):
            return _read_ollama_stream(response)
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        connection.close()

    if response.status >= 400:
        raise OllamaHTTPError(response.status, response_body)
    return json.loads(response_body)


def _read_ollama_stream(response: http.client.HTTPResponse) -> dict:
    if response.status >= 400:
        response_body = response.read().decode("utf-8", errors="replace")
        raise OllamaHTTPError(response.status, response_body)

    content_parts: list[str] = []
    thinking_parts: list[str] = []
    final_chunk: dict | None = None

    while True:
        line = response.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        chunk = json.loads(line.decode("utf-8"))
        final_chunk = chunk

        message = chunk.get("message", {})
        content = message.get("content")
        thinking = message.get("thinking")
        if isinstance(content, str):
            content_parts.append(content)
        if isinstance(thinking, str):
            thinking_parts.append(thinking)

        if chunk.get("done"):
            break

    if final_chunk is None:
        raise RuntimeError("Ollama returned an empty streaming response")

    final_message = dict(final_chunk.get("message", {}))
    final_message["content"] = "".join(content_parts)
    if thinking_parts:
        final_message["thinking"] = "".join(thinking_parts)
    final_chunk["message"] = final_message
    return final_chunk


def _ollama_think_value() -> bool | str:
    raw_value = os.getenv("ROBOT_BRAIN_OLLAMA_THINK", "false").strip().lower()
    if raw_value in {"true", "1", "yes", "on"}:
        return True
    if raw_value in {"false", "0", "no", "off"}:
        return False
    return raw_value


def _as_float(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
