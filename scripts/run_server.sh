#!/usr/bin/env bash
# Stable local server — no auto-reload (recommended for normal use)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH=.

echo "Starting stable server at http://127.0.0.1:8000 (no auto-reload)"
exec python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
