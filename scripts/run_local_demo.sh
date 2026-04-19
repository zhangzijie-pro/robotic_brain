#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # Keep this script ROS2-friendly without requiring ROS2 for the local demo.
  # shellcheck disable=SC1090
  set +u
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  set -u
fi

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"
export ROBOT_BRAIN_VLM_PROVIDER="${ROBOT_BRAIN_VLM_PROVIDER:-mock}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://host.docker.internal:11434}"
export ROBOT_BRAIN_OLLAMA_MODEL="${ROBOT_BRAIN_OLLAMA_MODEL:-qwen3-vl:2b}"
export ROBOT_BRAIN_VLM_DEADLINE_MS="${ROBOT_BRAIN_VLM_DEADLINE_MS:-30000}"

TASK="${1:-把桌上的红杯子拿给我}"

if [[ "$ROBOT_BRAIN_VLM_PROVIDER" == "ollama" ]]; then
  echo "Using Ollama at ${OLLAMA_HOST}"
  echo "Using model ${ROBOT_BRAIN_OLLAMA_MODEL}"
  echo "Using VLM deadline ${ROBOT_BRAIN_VLM_DEADLINE_MS}ms"
  TAGS_JSON="$(curl -fsS "${OLLAMA_HOST}/api/tags")" || {
    cat <<EOF
Could not reach Ollama at ${OLLAMA_HOST}.
Set OLLAMA_HOST to the address that works for your environment.
EOF
    exit 1
  }
  TAGS_FILE="$(mktemp)"
  trap 'rm -f "$TAGS_FILE"' EXIT
  printf '%s\n' "$TAGS_JSON" > "$TAGS_FILE"
  if ! python3 - "$ROBOT_BRAIN_OLLAMA_MODEL" "$TAGS_FILE" <<'PY'
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
Ollama is reachable, but model '${ROBOT_BRAIN_OLLAMA_MODEL}' is not installed.

Run:

  ollama pull ${ROBOT_BRAIN_OLLAMA_MODEL}

Or choose one of your installed models:

$(python3 - "$TAGS_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    payload = json.load(file)
for item in payload.get("models", []):
    print(f"  ROBOT_BRAIN_OLLAMA_MODEL={item.get('name')} ROBOT_BRAIN_VLM_PROVIDER=ollama ./scripts/run_local_demo.sh")
PY
)
EOF
    exit 1
  fi
fi

python3 -m robot_brain.demo \
  --provider "$ROBOT_BRAIN_VLM_PROVIDER" \
  --task "$TASK" \
  --pretty
