#!/usr/bin/env bash
# Dev server with reload — use only when editing code
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH=.

echo "Starting dev server with reload at http://127.0.0.1:8000"
exec python -m uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  --reload-delay 2 \
  --reload-dir backend \
  --reload-dir frontend \
  --reload-exclude '.venv' \
  --reload-exclude 'chroma_db' \
  --reload-exclude 'data' \
  --reload-exclude '.env'
