# Module 4 — Add AgentCore Observability

The last rung of the ladder. Your agent is **built** (Module 1) and **deployed** (Module 2). Now you make
it **observable**: see exactly what every request does — which tools it called, how many tokens it used,
how long each step took, and where it failed — in the **CloudWatch GenAI Observability** dashboard.

## The pleasant surprise: it's (almost) already on

Observability adds **zero agent code** — the agent here is **identical** to Module 2 (a drift-guard test
enforces that). It's three operational switches plus a look at the dashboard. Two distinct things must be
true: the agent must **emit** OTEL spans, and the runtime must be told to **deliver** them.

1. **Enable CloudWatch Transaction Search** — one-time, account-level; makes spans searchable in
   `/aws/spans`. Automated by `scripts/enable_transaction_search.py`.
2. **Deploy** — the container's `CMD` runs the agent under **`opentelemetry-instrument`** (from
   `aws-opentelemetry-distro`), so the deployed agent **emits** OTEL spans. (`agentcore.json` also keeps
   `instrumentation.enableOtel: true`.)
3. **Enable the per-runtime Tracing toggle** — a **console** action (AgentCore → Agent Runtime → your
   agent → Tracing → Edit → Enable) that **delivers** the agent's spans to CloudWatch. There is no public
   CLI/`agentcore.json` field for this on *runtime* resources yet, so it's one manual click per runtime.
4. **Invoke + view** — generate traffic (with a session id) and read the trace waterfall in the GenAI
   Observability dashboard.

> ⚠️ **The Tracing toggle (Step 3) is required.** Without it the agent emits spans but they never reach
> CloudWatch. It's a one-time, per-runtime console toggle.

## What you'll see in a trace

The runtime emits spans following **OpenTelemetry GenAI semantic conventions**, so the dashboard can
render them:

- `invoke_agent <name>` — the top-level span for one request
  - `gen_ai.operation.name`, `gen_ai.usage.input_tokens` / `output_tokens`, `session.id`
  - child `execute_tool <tool>` spans — each tool the agent called (Bash, Read, Task, Skill…)

You **read** these conventions to interpret a trace; you don't hand-write them (the runtime does).

## Prerequisites

- Everything from Module 2 (uv, Claude Code CLI, AWS creds, Bedrock access, `@aws/agentcore`, Docker
  daemon for the CLI, a CDK-bootstrapped account/region)
- **CloudWatch Transaction Search** enabled (the notebook / `scripts/enable_transaction_search.py` do this)

## Setup

```bash
cd module-4-observability
uv sync
cp .env.example .env
cp agentcore/aws-targets.example.json agentcore/aws-targets.json   # set your account + region
```

## The flow (the notebook walks through it)

```bash
# 1. One-time, account-level: enable Transaction Search (idempotent)
uv run python scripts/enable_transaction_search.py --region us-west-2

# 2. Deploy the already-observable agent (same as Module 2)
(cd agentcore/cdk && npm ci)   # ONE-TIME: install the CDK toolchain (node_modules isn't committed)
agentcore deploy -y

# 3. Generate traffic — pass a session id so the dashboard correlates the invocation
agentcore invoke --session-id "m4-demo-001" "What is our current runway?"

# 4. View traces:
#    GenAI dashboard → https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#gen-ai-observability
#    (or Transaction Search → log group /aws/spans). Allow ~2-10 min for indexing.

# 5. Cleanup
agentcore remove agent --name cos && agentcore deploy -y
```

> Transaction Search is **account-level** and is left enabled after cleanup — it's a one-time setup, not
> per-deployment.

## Testing

```bash
uv run --group test pytest            # FAST: drift-guard + config + Dockerfile + notebook + helper (no creds)
uv run --group test pytest -m slow    # SLOW: enable TS → deploy → invoke(session) → assert span appears → teardown
```

The slow tier auto-skips without AWS creds, and backs up/restores the tracked `agentcore.json` /
`aws-targets.json` so the run leaves the tree clean.

## Notes
- `agentcore/aws-targets.json` and `.env` are gitignored; commit only the `.example` files.
- This module reuses Module 1/2's agent bundle unchanged; a test asserts `agent.py` hasn't drifted.
