#!/usr/bin/env bash
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://host.docker.internal:11434}"
MODEL="${ROBOT_BRAIN_OLLAMA_MODEL:-qwen3-vl:2b}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_IMAGE="${ROBOT_BRAIN_DEMO_IMAGE:-${ROOT_DIR}/src/robot_brain/img.jpg}"

echo "Checking Ollama at ${OLLAMA_HOST}"
echo "Expected model: ${MODEL}"

TAGS_JSON="$(curl -fsS "${OLLAMA_HOST}/api/tags")"
printf '%s\n' "$TAGS_JSON" | python3 -m json.tool
TAGS_FILE="$(mktemp)"
trap 'rm -f "$TAGS_FILE"' EXIT
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
curl -fsS "${OLLAMA_HOST}/api/chat" \
  -H "Content-Type: application/json" \
  -d "$(python3 - "$MODEL" "$DEMO_IMAGE" <<'PY'
import base64
import json
from pathlib import Path
import sys

model = sys.argv[1]
image_path = Path(sys.argv[2])
message = {
    "role": "user",
    "content": "Return only JSON: {\"ok\": true, \"vision\": true}"
}
if image_path.exists():
    message["images"] = [
        base64.b64encode(image_path.read_bytes()).decode("ascii")
    ]

print(json.dumps({
    "model": model,
    "stream": False,
    "messages": [message]
}))
PY
)" | python3 -m json.tool

cat <<EOF

Ollama chat smoke test passed.
Image used: ${DEMO_IMAGE}

If you want to use a vision model and it is missing, run this on your host:

  ollama pull ${MODEL}

Then run the local demo from Docker:

  ROBOT_BRAIN_VLM_PROVIDER=ollama ./scripts/run_local_demo.sh
EOF
