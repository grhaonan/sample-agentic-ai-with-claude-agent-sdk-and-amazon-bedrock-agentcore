# Module 2 — Deploy to AgentCore Runtime

The second rung of the ladder: take the **exact same** Chief of Staff agent from Module 1 and deploy it
to **Amazon Bedrock AgentCore Runtime** — a managed, serverless runtime — reachable over HTTP.

We deploy it **bare**: just the agent in production, no memory, no observability dashboards yet. That's
deliberate — by the end you'll feel the statelessness limitation that Module 3 (Memory) fixes.

## The big idea: one agent, two front doors

Module 1 ran the agent locally via `send_query()`. Module 2 runs the **same** agent in the cloud via an
AgentCore entrypoint. Both share **one source of truth** for the agent's identity:

```
chief_of_staff_agent/
├── agent.py              # build_agent_options()  ← the agent's identity (ONE place)
│                         # send_query()           ← Module 1's local path
└── agent_agentcore.py    # @app.entrypoint invoke() ← Module 2's deploy path (thin wrapper)
```

`agent_agentcore.py` holds only the AgentCore plumbing (the `@app.entrypoint` decorator, payload parsing,
streaming). It calls the same `build_agent_options()` — so there is **no duplicated agent logic**. When
Module 3/4 change the agent, they change `build_agent_options()` once and both paths inherit it.

## Why a container (not a zip)

The Claude Agent SDK ships a ~218MB native CLI binary. Packaged as a zip (CodeZip), that binary lands
without the execute bit and the agent fails at runtime (`Permission denied`). So Module 2 uses a
**Container build** (`build: Container` in `agentcore.json`) — a Linux/ARM64 image that `pip install`s
the SDK fresh, giving the binary the right architecture and permissions. See `chief_of_staff_agent/Dockerfile`.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)**, **Claude Code CLI**, **AWS credentials**, **Bedrock model access** (as in Module 1)
- **Docker** running (the container image is built locally / via CodeBuild)
- **Node.js + the AgentCore CLI**: `npm install -g @aws/agentcore`
- The account/region must be **CDK-bootstrapped** (`cdk bootstrap`, one-time)

## Setup

```bash
cd module-2-deploy
uv sync                                  # local deps for testing + the invoke helper
cp .env.example .env                     # edit region / model if needed

# Point AgentCore at YOUR account/region:
cp agentcore/aws-targets.example.json agentcore/aws-targets.json
#   then edit aws-targets.json: set "account" to your 12-digit ID and "region"
```

## Deploy (the notebook walks through this)

```bash
agentcore validate                       # check config
agentcore dev                            # OPTIONAL: run the agent locally (http://localhost:8080)
agentcore deploy -y                      # build image → push to ECR → deploy runtime (via CDK)
agentcore invoke '{"prompt": "What is our current runway?"}'
agentcore status                         # show deployed runtime details
agentcore logs                           # stream CloudWatch logs
```

## Cleanup (avoid ongoing charges)

```bash
agentcore remove agent --name cos        # remove from config
agentcore deploy -y                      # apply removal → tears down the runtime/stack
```

## What's deployed

- **Runtime**: the `cos` agent (BYO Container, HTTP protocol). The execution IAM role (Bedrock invoke +
  CloudWatch Logs + X-Ray) is **created automatically by the CDK** — no manual role script needed.
- **Observability groundwork**: `instrumentation.enableOtel` is on and `aws-opentelemetry-distro` is in
  the image, so traces already flow to CloudWatch. We *view* them in **Module 4**.
- **Stateless**: each invocation is independent — the deployed agent doesn't remember you between calls.
  **Module 3** adds AgentCore Memory to fix that.

## Notes
- `agentcore/aws-targets.json` (your account ID) and `.env` are **gitignored**. Commit only the
  `.example` files.
- This module reuses Module 1's agent bundle. The two `agent.py` files are kept identical; a test guards
  against drift.
