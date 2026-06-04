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
| **1 — Local agent** | `query()` one-liner → `ClaudeSDKClient` + system prompt + `CLAUDE.md` + skills + multi-turn | ✅ **Built** |
| **2 — Deploy** | Wrap the agent in an AgentCore Runtime entrypoint, deploy, invoke over HTTP | ⬜ Not started |
| **3 — Memory** | AgentCore Memory (short-term events + long-term extraction) | ⬜ Not started |
| **4 — Observability** | OpenTelemetry / CloudWatch GenAI tracing (4a local, 4b agentcore) | ⬜ Not started |
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
├── advanced/text-to-sql-athena/   # 📦 the ORIGINAL BI/Student-Analytics workshop, archived as-is
└── LICENSE  CONTRIBUTING.md  CODE_OF_CONDUCT.md  .gitignore
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

## Testing (Module 1)

`module-1-local-agent/tests/` — run from inside that folder:

```bash
uv run --group test pytest            # FAST: static + scripts + hooks (no creds, ~seconds)
uv run --group test pytest -m slow    # SLOW: executes the whole notebook on Bedrock (needs creds, ~15 min)
```

Assertions are **structural/behavioral** (not exact text) to tolerate model non-determinism. The slow
tier auto-skips without AWS creds and backs up/restores `audit/` + `output_reports/` so the tree stays
clean. Both tiers verified green (fast 33 passed; slow 7 passed against live Bedrock).

## Current state (branch `refactoring`)

Done so far: archived the old BI code → built Module 1 (notebook + chief-of-staff agent + new
`financial-analysis` skill) → pinned deps + expanded teaching content → added the test harness.

**Next up: Module 2 — Deploy to AgentCore Runtime**, wrapping `chief_of_staff_agent/agent.py`.
