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
| **3 — Memory** | AgentCore Memory (short-term events + long-term extraction) | ⬜ Not started |
| **4 — Observability** | View agent traces in AgentCore Observability / CloudWatch (groundwork laid in M2) | ⬜ Not started |
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
- **Observability (Module 4) groundwork:** `enableOtel: true` + `aws-opentelemetry-distro` in the image
  means traces already export to CloudWatch. Module 4 should use the **SDK-native OTEL** path
  (verified: `claude-agent-sdk` 0.2.88 propagates W3C trace context to its CLI) — do NOT port the
  archived heavy manual `openinference`/hand-span approach.

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
uv run --group test pytest -m slow    # SLOW: real agentcore deploy+invoke round-trip (creds + Docker)
```

Verified green: Module 1 fast 33 + slow 7 (live Bedrock); Module 2 **fast 16** + **live deploy/invoke
verified** on us-west-2 (Container build via cloud CodeBuild; invoke had no `Permission denied` — the
CodeZip bundled-binary bug is fixed by the Container path).

> **Deploy note:** local Docker is NOT needed — the `@aws/agentcore` Container build runs in the cloud
> (CodeBuild, ARM64). `agentcore deploy` reads the target from `agentcore/aws-targets.json` (gitignored);
> the account/region must be CDK-bootstrapped first (`cdk bootstrap`).

## Current state (branch `refactoring`)

Done: archived old BI code → Module 1 (notebook + agent + skill + tests) → Module 2 (refactored
`build_agent_options()`, thin AgentCore entrypoint, Container Dockerfile, `agentcore.json`, notebook,
tests) → **Module 2 live-verified end-to-end on AWS** (deploy + invoke + teardown). All work is
uncommitted, in the working tree.

**Next up:** Module 3 — AgentCore Memory (give the deployed, currently-stateless agent cross-session
memory).
