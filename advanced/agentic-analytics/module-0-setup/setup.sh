#!/bin/bash
# Module 0 — stand up the data layer (S3 + Athena) in ONE run.
set -e
cd "$(dirname "$0")"
MODULE_NAME="agentic-analytics-module-0-setup"

# .env
[ -f .env ] || cp .env.example .env

# Python dependencies
uv sync

# Register Jupyter kernel (so the notebook can run with these deps)
.venv/bin/python -m ipykernel install \
  --user --name "$MODULE_NAME" --display-name "$MODULE_NAME"

# Create the infrastructure (idempotent — safe to re-run).
echo ""
echo "Running infrastructure setup…"
uv run python scripts/setup_infrastructure.py

echo ""
echo "✅ Module 0 complete. Select the '$MODULE_NAME' kernel if you open the notebook."
