#!/bin/bash
# Module 1 — local text-to-SQL agent. No AWS deploy here, just a local venv.
set -e
cd "$(dirname "$0")"
MODULE_NAME="agentic-analytics-module-1-local-agent"

# .env
[ -f .env ] || cp .env.example .env

# Python dependencies
uv sync

# Register Jupyter kernel
.venv/bin/python -m ipykernel install \
  --user --name "$MODULE_NAME" --display-name "$MODULE_NAME"

echo ""
echo "✅ Setup complete — select the '$MODULE_NAME' kernel in the kernel picker (top-right)."
echo "   (Run Module 0 first if you haven't — this agent queries the Athena tables it creates.)"
