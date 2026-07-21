#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH=.

exec python -m uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  --reload-dir backend \
  --reload-dir frontend \
  --reload-exclude '.venv/*' \
  --reload-exclude 'chroma_db/*' \
  --reload-exclude 'data/*'
