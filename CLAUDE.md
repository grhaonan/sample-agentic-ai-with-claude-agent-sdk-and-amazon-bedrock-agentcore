# Project: Agentic AI with Claude Agent SDK + Amazon Bedrock AgentCore

This repo holds the **code** for a hands-on workshop. The **instructions** live in a separate
Workshop Studio repo (`democratizing-business-intelligence-by-using-claude-agent-sdk-on-amazon-bedrock-agentcore`),
which has already been refactored into the new "ladder" structure below. This repo is being rebuilt
to match it.

> This file is a **project record for developers / future sessions** — what the repo is and where we
> are. It is *not* an agent runtime file. The agent's own context lives at
> `module-1-local-agent/chief_of_staff_agent/CLAUDE.md` (loaded by the SDK via `setting_sources`).

## The workshop = a progressive ladder (use-case-agnostic)

| Module | Teaches | Status in this repo |
|--------|---------|---------------------|
| **1 — Local agent** | `query()` one-liner → `ClaudeSDKClient` + system prompt + `CLAUDE.md` + skills + multi-turn | ✅ **Built & tested** |
| **2 — Deploy** | Wrap the agent in an AgentCore Runtime entrypoint, deploy (Container/ECR), invoke over HTTP | ✅ **Built & live-verified (us-west-2)** |
| **4 — Observability** | View agent traces in AgentCore Observability / CloudWatch GenAI dashboard | ✅ **Built & live-verified (us-west-2)** |
| **3 — Memory** | AgentCore Memory (short-term events + long-term extraction) | ⬜ Not started (next) |
| **Advanced (optional)** | Track 1: Text-to-SQL on Athena · Track 2: Follow-up questions | 📦 Archived (see below) |

The running example for Modules 1–4 is the **Chief of Staff agent** (fictional startup "TechStart Inc" —
runway / burn / hiring analysis), adapted from the Claude cookbook. It needs **near-zero infra**: just
AWS credentials + Amazon Bedrock model access (no Athena/S3).

## Repo layout

```
.
├── module-1-local-agent/          # ✅ Module 1 — self-contained, uv-managed
│   ├── module-1-local-agent.ipynb # single notebook: Part 1A → 1B → "all together"
│   ├── chief_of_staff_agent/      # the agent's body (read from disk by the SDK)
│   │   ├── agent.py               # send_query() entrypoint (Module 2 will deploy this)
│   │   ├── CLAUDE.md              # agent runtime context (NOT this file)
│   │   ├── .claude/{skills,agents,commands,hooks,output-styles,settings.json}
│   │   ├── scripts/  financial_data/  audit/  output_reports/
│   ├── utils/                     # HTML render helpers (from cookbook)
│   ├── tests/                     # pytest harness (fast + slow tiers) — see Testing
│   ├── pyproject.toml  README.md  .env.example
├── module-2-deploy/                # ✅ Module 2 — deploy the SAME agent to AgentCore Runtime
│   ├── module-2-deploy.ipynb       # guided notebook: configure → dev → deploy → invoke → cleanup
│   ├── chief_of_staff_agent/       # COPY of Module 1's bundle + agent_agentcore.py (thin entrypoint)
│   │   ├── agent_agentcore.py      # @app.entrypoint — reuses build_agent_options() (no dup logic)
│   │   ├── Dockerfile              # Linux/arm64; pip-installs SDK fresh (CodeZip can't — see below)
│   │   └── pyproject.toml          # in-container deps (SDK + bedrock-agentcore + aws-otel-distro)
│   ├── agentcore/                  # @aws/agentcore project (agentcore.json, CDK, aws-targets.example.json)
│   ├── tests/                      # fast (reuse/config/static) + slow (live deploy) tiers
│   ├── pyproject.toml  README.md  .env.example
├── module-4-observability/         # ✅ Module 4 — trace the deployed agent in CloudWatch
│   ├── module-4-observability.ipynb # guided: Transaction Search → deploy → Tracing toggle → invoke → view
│   ├── chief_of_staff_agent/        # SAME bundle as M2; Dockerfile CMD wraps `opentelemetry-instrument`
│   ├── scripts/enable_transaction_search.py  # idempotent account-level setup
│   ├── agentcore/  tests/  pyproject.toml  README.md  .env.example
├── advanced/text-to-sql-athena/   # 📦 the ORIGINAL BI/Student-Analytics workshop, archived as-is
└── CLAUDE.md  LICENSE  CONTRIBUTING.md  CODE_OF_CONDUCT.md  .gitignore
```

## Conventions established

- **Bedrock, not the Anthropic API.** No hardcoded `model=` in agent code — the model comes from
  `ANTHROPIC_MODEL` + `CLAUDE_CODE_USE_BEDROCK=1` in `.env`. (Note: a pre-set shell `AWS_REGION` and the
  Claude Code CLI's own model config can override `.env`, since `load_dotenv()` doesn't override existing
  env vars.)
- **Each module is self-contained**, with its own `pyproject.toml` and local `.venv` (uv). There is no
  top-level Python project.
- **Dependencies are pinned exactly (`==`)**, not `>=` — runtime and test deps alike.
- **Skills vs. CLAUDE.md vs. subagents** are taught as three distinct mechanisms: procedure / always-on
  facts / task delegation.
- Setup steps (`uv sync`, kernel install) stay in **README + a markdown cell**, not code cells (they
  create the very kernel the notebook runs in).

### Module 2 / deployment decisions (from a real AWS spike)
- **Tooling = the new `@aws/agentcore` npm CLI** (`agentcore create/add/deploy/invoke/remove`,
  config = `agentcore/agentcore.json`, CDK-based). The old `bedrock-agentcore-starter-toolkit` is
  **deprecated** — do not use it.
- **Build type = Container, NOT CodeZip.** The Claude Agent SDK bundles a ~218MB native CLI
  (`claude_agent_sdk/_bundled/claude`). With CodeZip the deploy *succeeds* but `invoke` fails:
  `Permission denied: .../_bundled/claude` (zip strips the execute bit). Container `pip install`s the SDK
  fresh on Linux/arm64 → correct arch + perms. (Proven both ways in the spike.)
- **Reuse = shared `build_agent_options()`** in `agent.py` (single source of truth). The deploy entrypoint
  `agent_agentcore.py` is thin: `@app.entrypoint` + payload parse + streaming, calling
  `build_agent_options()`. A test (`test_reuse.py`) guards against drift / duplicated logic.
- **Bundle reuse mechanism:** Module 2 holds a **copy** of Module 1's `chief_of_staff_agent/` (Container
  build needs all code under one `codeLocation`). A drift-guard test asserts the two `agent.py` are
  byte-identical. *(Open question for review: copy vs. a shared package — see morning summary.)*
- **Execution IAM role is auto-created by the CDK** (Bedrock invoke + CloudWatch Logs + X-Ray) — no manual
  role script needed.
- **`agentcore.json` natively supports `memories[]` (Module 3) and `instrumentation.enableOtel` (Module
  4)** — both are config additions, not rework.
- **Account ID hygiene:** `agentcore/aws-targets.json` (real 12-digit account) is **gitignored**; commit
  only `aws-targets.example.json`. Participants copy + fill it in.
### Module 4 / observability decisions (live-verified on us-west-2)
Observability adds **zero agent code** (same bundle as M2; drift-guard test enforces it). The archived
745-line manual `openinference`/hand-span approach is **obsolete** — not used. Three switches make a
trace appear in the CloudWatch GenAI dashboard, and **all three are required** (proven by trial):
1. **Account-level CloudWatch Transaction Search** — one-time; makes spans searchable in `/aws/spans`.
   Automated by `scripts/enable_transaction_search.py` (idempotent).
2. **Container EMITS spans** — the Dockerfile `CMD` must run under **`opentelemetry-instrument`**
   (from `aws-opentelemetry-distro`) + ADOT env (`AGENT_OBSERVABILITY_ENABLED=true`, `OTEL_*`).
   ⚠️ **Gotcha:** for a BYO-Container with a custom CMD the runtime does **NOT** auto-inject the OTEL
   wrapper — we add it ourselves. (M2's Dockerfile comment claiming auto-injection was wrong.)
3. **Per-runtime Tracing toggle DELIVERS spans** — a **console** action (AgentCore → Agent Runtime →
   agent → Tracing → Edit → Enable). **No public CLI/`agentcore.json` field** for runtime resources
   (the SDK delivery API only covers memory/gateway). So Module 4's notebook teaches it as a one-time
   manual toggle step. Without it, the agent emits spans but they never reach CloudWatch.
- **End-to-end proof:** after all three + `agentcore invoke --session-id <33+ chars>`, a `POST /invocations`
  span with the session id landed in `/aws/spans` within ~2 min. (Session ids must be **≥33 chars**.)
- **Other gotcha:** pin `aws-cdk-lib` **exactly** in `agentcore/cdk/package.json` — a floating `^` let it
  resolve to a lib newer than the bundled `aws-cdk` CLI could read (CDK synth "schema version" error).

## Testing

Each module has its own `tests/` (run from inside the module folder). Assertions are
**structural/behavioral** (not exact text) to tolerate model non-determinism; the slow tier auto-skips
when prerequisites are missing.

```bash
# Module 1
uv run --group test pytest            # FAST: static + scripts + hooks (no creds)
uv run --group test pytest -m slow    # SLOW: executes the notebook on Bedrock (creds, ~15 min)

# Module 2
uv run --group test pytest            # FAST: reuse/drift-guard + config + Dockerfile + notebook (no creds/Docker)
uv run --group test pytest -m slow    # SLOW: real agentcore deploy+invoke round-trip (creds)

# Module 4
uv run --group test pytest            # FAST: drift-guard + enableOtel/OTEL-wrapper config + TS helper + notebook
uv run --group test pytest -m slow    # SLOW: enable TS → deploy → invoke → assert OTEL active; span check best-effort
```

Verified green: Module 1 fast 33 + slow 7 (live Bedrock); Module 2 **fast 16** + live deploy/invoke on
us-west-2; Module 4 **fast 15** + **live-verified end-to-end** on us-west-2 (a `POST /invocations` span
with our session id reached `/aws/spans` after enabling the runtime Tracing toggle).

> **Deploy note:** local Docker is NOT needed — the `@aws/agentcore` Container build runs in the cloud
> (CodeBuild, ARM64). `agentcore deploy` reads the target from `agentcore/aws-targets.json` (gitignored);
> the account/region must be CDK-bootstrapped first (`cdk bootstrap`).

## Current state (branch `refactoring`)

Done: archived old BI code → Module 1 → Module 2 (deploy, live-verified) → **Module 4 (observability),
live-verified end-to-end on AWS** (Transaction Search + OTEL-wrapped container + runtime Tracing toggle →
trace in `/aws/spans`). We built Module 4 before Module 3 because observability only depends on the
deployed agent, and the memory design wasn't finalized. All Module 4 work is uncommitted, in the working
tree.

**Next up:** Module 3 — AgentCore Memory (give the deployed, currently-stateless agent cross-session
memory). `agentcore.json` already has a first-class `memories[]` block for this.
