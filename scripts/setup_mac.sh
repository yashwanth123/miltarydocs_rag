#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Project: $ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed."
  exit 1
fi

echo "==> Python: $(python3 --version)"

if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment..."
  python3 -m venv .venv
fi

echo "==> Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Upgrading pip..."
python -m pip install --upgrade pip

echo "==> Installing dependencies (this may take several minutes)..."
python -m pip install -r requirements.txt

echo "==> Verifying imports..."
python - <<'PY'
import dotenv
import chromadb
import fastapi
print("Dependencies OK")
PY

mkdir -p data

echo
echo "Setup complete."
echo
echo "Next steps:"
echo "  1. Copy your files into data/  (.pdf, .txt, .docx)"
echo "  2. source .venv/bin/activate"
echo "  3. export PYTHONPATH=."
echo "  4. python scripts/ingest_documents.py --reset"
echo "  5. uvicorn backend.main:app --reload"
echo "  6. Open http://127.0.0.1:8000/"
