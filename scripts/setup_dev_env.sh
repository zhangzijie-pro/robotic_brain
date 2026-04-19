#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

if python3 -m pip --version >/dev/null 2>&1; then
  if python3 -m pip install -e .; then
    INSTALL_STATUS="editable install succeeded"
  else
    INSTALL_STATUS="editable install failed; PYTHONPATH fallback is still available"
  fi
else
  INSTALL_STATUS="pip is not available; PYTHONPATH fallback is active"
fi

cat <<EOF

Development environment is ready.
Status: $INSTALL_STATUS

For the current shell only:

  export PYTHONPATH="$ROOT_DIR/src:\${PYTHONPATH:-}"

Recommended run commands:

  python3 -m robot_brain.demo --pretty
  ./scripts/run_local_demo.sh
  PYTHONPATH=src python3 tests/unit/test_world_model.py

Avoid running package files directly, such as:

  python3 src/robot_brain/agents/vision_agent.py

Use module mode instead when a module has an entrypoint:

  python3 -m robot_brain.demo --pretty
EOF
