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
| **3 — Memory** | AgentCore Memory (short-term events + long-term extraction); single-tenant | ✅ **Built & live-verified (us-west-2): deploy + cross-session recall round-trip** |
| **4 — Observability** | View agent traces in AgentCore Observability / CloudWatch GenAI dashboard | ✅ **Built & live-verified (us-west-2)** |
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
├── module-3-memory/                # ✅ Module 3 — give the SAME agent cross-session memory (single-tenant)
│   ├── module-3-memory.ipynb        # guided: deploy → session A (state fact) → session B (recall) → A/B → inspect LTM → cleanup
│   ├── chief_of_staff_agent/        # M2 bundle + memory/session.py + memory-aware agent_agentcore.py
│   │   ├── memory/session.py        # get_memory(): retrieve_context() (STM list_events + LTM retrieve) + record_turn() (create_event)
│   │   └── agent_agentcore.py       # @app.entrypoint invoke(payload, context) — recall → run → record; {"memory":false} A/B toggle
│   ├── agentcore/                   # agentcore.json with memories[] (SEMANTIC facts + USER_PREFERENCE prefs)
│   ├── SPIKE_NOTES.md               # Phase-0 live findings (IAM auto-wired, LTM latency, verified boto3 shapes)
│   ├── tests/  pyproject.toml  README.md  .env.example
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
### Module 3 / memory decisions (Phase-0 spike-verified on us-west-2; see `module-3-memory/SPIKE_NOTES.md`)
Chosen approach = **AgentCore Memory** (over the Runtime persistent filesystem — verified per-session/
ephemeral, the opposite of the mandate — and over a DIY SessionStore/vector store — re-implements a
managed service). **Single-tenant** (one fixed `actor_id = "techstart-cos"`); multi-tenant is documented
as a follow-on, not built.
- **`agent.py` gained one additive param: `system_prompt_suffix`** (backported into Module 1 and re-synced
  to ALL bundle copies — the byte-identical drift-guard still passes). Memory is injected via
  `build_agent_options(system_prompt_suffix=recalled_text)`, NOT a forked `system_prompt=` — which also
  keeps `test_reuse.py`'s "no `system_prompt=` in the entrypoint" guard green. ⚠️ This means Module 1's
  `agent.py` is **no longer the same bytes as before this module** — all four copies changed together.
- **Entrypoint is now `invoke(payload, context)` (2 args).** The runtime only delivers the request context
  (→ `context.session_id`) when the 2nd param is literally named `context` (verified in
  `bedrock_agentcore/runtime/app.py::_takes_context`). `memory/session.py` is the only net-new agent code.
- **IAM is AUTO-WIRED — no manual policy.** `agentcore deploy` with a populated `memories[]` grants the
  runtime role the memory data-plane actions (CreateEvent/ListEvents/ListSessions/RetrieveMemoryRecords/…)
  and injects the env var **`MEMORY_<UPPERCASE_NAME>_ID`** (for `CosMemory` → `MEMORY_COSMEMORY_ID`).
  Verified by reading the installed `@aws/agentcore-cdk` (`AgentCoreApplication.wireMemoriesToAgents()` →
  `AgentCoreMemory.grant()`).
- **Two layers, and the latency gotcha that shapes the demo:** short-term events (`create_event`/
  `list_events`) are **immediate**; long-term extraction (SEMANTIC facts + USER_PREFERENCE) is
  **async** (measured: prefs ~64s, facts ~80s after a write; memory ~150s to `ACTIVE`). So **live
  cross-session recall rides on short-term `list_events`** of the actor's prior sessions; LTM is the
  "learned over time" inspect beat. `retrieve_context()` queries both.
- **Verified boto3 shapes (NOT the guide's pseudocode):** `create_event` payload key is **`conversational`**
  (not `conversationalMessage`), `content` is a struct `{"text": ...}`, `eventTimestamp` is **required**,
  role enum is **`USER`/`ASSISTANT`**. `retrieve_memory_records` takes a **top-level `namespace`** +
  `searchCriteria={"searchQuery","topK"}`. `list_events` **requires `sessionId`**; `list_sessions` returns
  `sessionSummaries[].{sessionId,actorId,createdAt}`. USER_PREFERENCE records come back JSON-wrapped
  (`{"context": "..."}`); SEMANTIC facts are plain text — `_unwrap_record_text` handles both.
- **`eventExpiryDuration` min is 7** (installed CDK zod), not the 3 the older guide text claims; we use 7.
- **Graceful degradation:** unset `MEMORY_COSMEMORY_ID` (e.g. local `agentcore dev`, where Memory is
  unavailable) or any data-plane error → `_NullMemory`, agent runs stateless (never crashes).
- **Demo honesty:** the recalled value (`$42.5M`) is **invented in-session** because the bundle's
  `CLAUDE.md` hardcodes a **$30M** Series B (line 40) — reusing $30M would prove nothing. Proof is a
  same-deployment **A/B** (`{"memory": false}`), not a comparison against the M2 deployment.
- **LIVE-VERIFIED (us-west-2):** the slow test (`test_deploy_live.py`) passed end-to-end in ~11 min —
  deploy provisioned runtime + CosMemory, session A wrote the `$42.5M` fact, **session B recalled it**
  (no AccessDenied → IAM auto-wiring confirmed live), then teardown destroyed both resources (0 memories /
  0 runtimes after) and restored the config snapshot.
- **CDK reproducibility gotcha (pre-existing, repo-wide):** `agentcore deploy` runs `npm run build` (`tsc`),
  which needs the CDK project's `node_modules` AND `lib/cdk-stack.ts`. BOTH are **gitignored**
  (`cdk/.gitignore` ignores `node_modules`; root `.gitignore:17` ignores `lib/`), so a fresh git checkout
  of any module's `agentcore/cdk/` can't deploy until you `npm ci` there and restore `lib/cdk-stack.ts`.
  M2/M4 only deploy because their copies exist locally from prior runs. For M3 I had to `npm ci` and copy
  `lib/cdk-stack.ts` from M2. **Flag for a repo-wide fix** (commit `lib/cdk-stack.ts`, or regenerate it +
  `npm ci` as a documented setup step). The deploy also fails fast with `sh: tsc: command not found` when
  `node_modules` is absent — a clear signal of this.

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

# Module 3
uv run --group test pytest            # FAST: reuse/drift-guard + suffix/context + memory-helper logic (fake client) + memories[] config + notebook
uv run --group test pytest -m slow    # SLOW: deploy → session A writes → session B recalls (STM) → assert no AccessDenied

# Module 4
uv run --group test pytest            # FAST: drift-guard + enableOtel/OTEL-wrapper config + TS helper + notebook
uv run --group test pytest -m slow    # SLOW: enable TS → deploy → invoke → assert OTEL active; span check best-effort
```

Verified green: Module 1 fast 33 + slow 7 (live Bedrock); Module 2 **fast 16** + live deploy/invoke on
us-west-2; Module 3 **fast 31** (reuse 9 + config 7 + memory-helper 9 + notebook 6) + **slow 2 live-verified
on us-west-2** (deploy runtime+CosMemory → session A writes `$42.5M` → session B recalls it, no AccessDenied →
IAM auto-wiring confirmed → teardown destroyed both; ~11 min); Module 4 **fast 15** + **live-verified
end-to-end** on us-west-2 (a `POST /invocations` span with our session id reached `/aws/spans` after
enabling the runtime Tracing toggle).

> **Deploy note:** local Docker is NOT needed — the `@aws/agentcore` Container build runs in the cloud
> (CodeBuild, ARM64). `agentcore deploy` reads the target from `agentcore/aws-targets.json` (gitignored);
> the account/region must be CDK-bootstrapped first (`cdk bootstrap`).

## Current state (branch `refactoring`)

Done: archived old BI code → Module 1 → Module 2 (deploy, live-verified) → Module 4 (observability,
live-verified) → **Module 3 (memory), built + fast-tested (31 green) + LIVE-VERIFIED end-to-end on
us-west-2** (deploy + cross-session recall round-trip; see Module 3 decisions above). Module 3 is
**single-tenant** and reuses the M2 bundle + the new `memory/session.py`; the `system_prompt_suffix`
backport touched Module 1's `agent.py` and was re-synced to all bundle copies (drift-guard still green).
Modules 1, 2, 4 are committed/pushed to `origin/refactoring`.

**Uncommitted in the working tree (this session):** Module 3 (new `module-3-memory/`), the
`system_prompt_suffix` change to `module-{1,2,4}/.../agent.py`, and this CLAUDE.md update. **Not yet
committed** — Module 3 is complete and live-verified; ready to commit when you are.

### Python version is pinned to 3.11 everywhere (parity)
Local dev, the deployed container, and the (cosmetic-for-Container) runtime config all say 3.11:
- **Local dev:** committed `.python-version` = `3.11.14` per MODULE folder (uv's native pin; `requires-python`
  is only a range and let the venvs drift to 3.12). `3.11.15` doesn't exist — 3.11.14 is the newest 3.11 build.
- **Deployed container:** bundle `Dockerfile` `FROM python:3.11-slim-bookworm` — this is the ONLY thing that
  sets the deployed Python for a Container build. **Live-verified on us-west-2** (M2 deploy+invoke on the 3.11
  image passed, then torn down).
- **`agentcore.json` `runtimeVersion: PYTHON_3_11`** — set for consistency, but **the CDK IGNORES it for
  Container builds** (verified in `AgentCoreRuntime.js`: `runtimeVersion` only feeds the CodeZip
  `codeConfiguration.runtime`; Container uses just `containerConfiguration.containerUri`). The Dockerfile wins.
- Bundles keep `requires-python = ">=3.11"` (a floor, fine).

**Open items / repo-wide quirks (one resolved this session):**
1. ✅ **RESOLVED — `Dockerfile` un-ignored & committed.** Removed the global `Dockerfile` ignore so the three
   bundle Dockerfiles (now `python:3.11`) are tracked. A fresh clone now has them; `test_dockerfile_*` passes.
2. **Still open — CDK project isn't reproducible from git:** `agentcore/cdk/lib/cdk-stack.ts` is gitignored
   (`.gitignore` `lib/`) and `node_modules` is gitignored — so `agentcore deploy` (`tsc` build) fails on a fresh
   checkout until you restore `lib/cdk-stack.ts` and `npm ci`. Symptom: `sh: tsc: command not found`.
