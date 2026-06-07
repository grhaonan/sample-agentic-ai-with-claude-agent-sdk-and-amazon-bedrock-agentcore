#!/bin/bash
set -e
cd "$(dirname "$0")"
MODULE_NAME="agentic-analytics-module-3-follow-up"

# .env
[ -f .env ] || cp .env.example .env

# Node.js 20 + AgentCore CLI (idempotent)
if ! command -v agentcore &>/dev/null; then
  curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
  sudo yum install -y nodejs-20.20.2
  sudo npm install -g @aws/agentcore@0.17.0
fi
(cd agentcore/cdk && npm ci)

# Python dependencies
uv sync

# Register Jupyter kernel
.venv/bin/python -m ipykernel install \
  --user --name "$MODULE_NAME" --display-name "$MODULE_NAME"

echo ""
echo "✅ Setup complete — now select the '$MODULE_NAME' kernel in the kernel picker (top-right)."
echo "   (Run Module 0 first — this agent queries the Athena tables it creates.)"
