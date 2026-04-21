#!/usr/bin/env bash
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
MODEL="${ROBOT_BRAIN_OLLAMA_MODEL:-${ROBOT_BRAIN_OLLAMA_VISION_MODEL:-qwen3-vl:2b}}"
OLLAMA_THINK="${ROBOT_BRAIN_OLLAMA_THINK:-false}"
OLLAMA_NUM_PREDICT="${ROBOT_BRAIN_OLLAMA_NUM_PREDICT:-192}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_IMAGE="${ROBOT_BRAIN_DEMO_IMAGE:-${ROOT_DIR}/src/robot_brain/img.jpg}"
PAYLOAD_FILE="$(mktemp)"

echo "Checking Ollama at ${OLLAMA_HOST}"
echo "Expected model: ${MODEL}"
echo "Think mode: ${OLLAMA_THINK}"
echo "Num predict: ${OLLAMA_NUM_PREDICT}"

TAGS_JSON="$(curl -fsS "${OLLAMA_HOST}/api/tags")"
printf '%s\n' "$TAGS_JSON" | python3 -m json.tool
TAGS_FILE="$(mktemp)"
trap 'rm -f "$TAGS_FILE" "$PAYLOAD_FILE"' EXIT
printf '%s\n' "$TAGS_JSON" > "$TAGS_FILE"

if ! python3 - "$MODEL" "$TAGS_FILE" <<'PY'
import json
import sys

model = sys.argv[1]
with open(sys.argv[2], encoding="utf-8") as file:
    payload = json.load(file)
models = {item.get("name") for item in payload.get("models", [])}
sys.exit(0 if model in models else 1)
PY
then
  cat <<EOF

Ollama is reachable, but model '${MODEL}' is not installed.

Installed models:
$(python3 - "$TAGS_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    payload = json.load(file)
for item in payload.get("models", []):
    print(f"  - {item.get('name')}")
PY
)

Fix one of these:

  ollama pull ${MODEL}

or run the demo with an installed model:

  ROBOT_BRAIN_VLM_PROVIDER=ollama \\
  ROBOT_BRAIN_OLLAMA_MODEL=<installed-model> \\
  ./scripts/run_local_demo.sh
EOF
  exit 1
fi

echo
echo "Running /api/chat smoke test with ${MODEL}"
python3 - "$MODEL" "$DEMO_IMAGE" "$TAGS_FILE" "$PAYLOAD_FILE" "$OLLAMA_THINK" "$OLLAMA_NUM_PREDICT" <<'PY'
import base64
import json
from pathlib import Path
import sys

model = sys.argv[1]
image_path = Path(sys.argv[2])
tags_path = Path(sys.argv[3])
payload_path = Path(sys.argv[4])

vision_markers = ("vl", "vision", "llava", "bakllava", "minicpm-v", "moondream")
with tags_path.open(encoding="utf-8") as file:
    tags = json.load(file)

model_info = next(
    (item for item in tags.get("models", []) if item.get("name") == model),
    {},
)
families = model_info.get("details", {}).get("families") or []
model_tokens = " ".join([model, *families]).lower().replace(".", "")
can_try_image = any(marker in model_tokens for marker in vision_markers)

message = {
    "role": "user",
    "content": "Return only JSON: {\"ok\": true}"
}
if can_try_image and image_path.exists():
    message["images"] = [
        base64.b64encode(image_path.read_bytes()).decode("ascii")
    ]
    message["content"] = "Return only JSON: {\"ok\": true, \"vision\": true}"

payload_path.write_text(
    json.dumps({
        "model": model,
        "stream": True,
        "think": sys.argv[5].lower() == "true",
        "messages": [message],
        "options": {"temperature": 0.1, "num_predict": int(sys.argv[6])},
    }),
    encoding="utf-8",
)

if can_try_image:
    print(f"Model family looks vision-capable; image included: {image_path.exists()}")
else:
    print("Model family looks text-only; running text chat smoke test without image.")
PY

curl -fsS "${OLLAMA_HOST}/api/chat" \
  -H "Content-Type: application/json" \
  --data-binary "@${PAYLOAD_FILE}" | python3 - <<'PY'
import json
import sys

content_parts = []
thinking_parts = []
last_chunk = None

for raw_line in sys.stdin:
    raw_line = raw_line.strip()
    if not raw_line:
        continue
    chunk = json.loads(raw_line)
    last_chunk = chunk
    message = chunk.get("message", {})
    if isinstance(message.get("content"), str):
        content_parts.append(message["content"])
    if isinstance(message.get("thinking"), str):
        thinking_parts.append(message["thinking"])
    if chunk.get("done"):
        break

if last_chunk is None:
    raise SystemExit("empty response from Ollama")

summary = {
    "model": last_chunk.get("model"),
    "content": "".join(content_parts),
    "thinking_chars": len("".join(thinking_parts)),
    "total_duration": last_chunk.get("total_duration"),
    "eval_count": last_chunk.get("eval_count"),
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY

cat <<EOF

Ollama chat smoke test passed.
Configured image path: ${DEMO_IMAGE}

If you want image understanding, install and select a vision-capable model, for example:

  ollama pull qwen3-vl:2b
  ROBOT_BRAIN_OLLAMA_MODEL=qwen3-vl:2b ./scripts/check_ollama_vision.sh

Then run the local demo:

  ROBOT_BRAIN_VLM_PROVIDER=ollama ./scripts/run_local_demo.sh
EOF
