#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Project: $ROOT_DIR"

PYTHON_BIN="python3"
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
  echo "==> Using Python 3.12 (recommended on macOS)"
else
  echo "==> Using default python3"
  echo "    Tip: if install fails on Python 3.13, run: brew install python@3.12"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN is not installed."
  exit 1
fi

echo "==> Python: $($PYTHON_BIN --version)"

if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
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
import pypdf
import pydantic
print(f"Dependencies OK (pydantic {pydantic.__version__})")
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
echo "     (loads public recruit guides + any files in data/)"
echo "  5. bash scripts/run_server.sh"
echo "  6. Open http://127.0.0.1:8000/"
