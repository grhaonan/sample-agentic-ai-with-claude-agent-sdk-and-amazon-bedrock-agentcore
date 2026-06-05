# Module 3 — Add AgentCore Memory

The memory rung of the ladder: take the **same** deployed Chief of Staff agent from Module 2 and give it
**cross-session memory** with **Amazon Bedrock AgentCore Memory**. The agent that forgot you between calls
now remembers what you discussed in a previous session.

**Single-tenant** by design — one fixed user (`techstart-cos`) — so the focus stays on *how memory works*.
Per-user isolation (multi-tenant) is a deliberate follow-on, not covered here.

## The big idea: memory without forking the agent

`build_agent_options()` in `agent.py` is still the **one source of truth** — byte-identical to Module 1
(a test guards it). Module 3 layers memory on through two thin pieces:

```
chief_of_staff_agent/
├── agent.py              # build_agent_options()  ← unchanged identity (ONE place)
├── memory/
│   └── session.py        # get_memory(): retrieve_context() + record_turn()  ← the only new agent code
└── agent_agentcore.py    # @app.entrypoint invoke(payload, context)          ← recall → run → record
```

- **Turn start:** `retrieve_context()` recalls what we know about the user and the entrypoint injects it
  via the additive `build_agent_options(system_prompt_suffix=...)` — so the canonical system prompt is
  never forked.
- **Turn end:** `record_turn()` persists the exchange so future sessions can recall it.

## Two layers of memory

| Layer | API | Holds | Available |
|---|---|---|---|
| **Short-term** | `create_event` / `list_events` | Raw turns per `(actor, session)` | **Immediately** |
| **Long-term** | extraction → `retrieve_memory_records` | Distilled **facts** + **preferences** | **After async extraction (~1–2 min)** |

⚠️ **Long-term extraction is asynchronous** (measured on us-west-2: preferences ~64s, facts ~80s after a
write; the memory itself takes ~150s to become `ACTIVE`). So **live cross-session recall rides on the
short-term layer** (instant), and the long-term layer is the "it learned about you over time" beat we
inspect after a gap. See `SPIKE_NOTES.md` for the full measurements and verified API shapes.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)**, **Claude Code CLI**, **AWS credentials**, **Bedrock model access** (as in Module 1)
- **Node.js + the AgentCore CLI**: `npm install -g @aws/agentcore`
- The account/region must be **CDK-bootstrapped** (`cdk bootstrap`, one-time)
- **Memory is cloud-only** — it is **not** available under `agentcore dev`. The loop here is
  **deploy → invoke → observe**.

## Setup

```bash
cd module-3-memory
uv sync                                  # local deps for testing + the invoke helper

# Point AgentCore at YOUR account/region:
cp agentcore/aws-targets.example.json agentcore/aws-targets.json
#   then edit aws-targets.json: set "account" to your 12-digit ID and "region"
```

## Deploy & demo (the notebook walks through this)

```bash
agentcore validate                       # check config (memories[] now populated)
agentcore deploy -y                      # provisions the runtime AND the CosMemory resource;
                                         #   auto-wires memory IAM + injects MEMORY_COSMEMORY_ID
```

Then in the notebook: state a fact in **session A**, recall it from a **new session B** (cross-session
"aha"), prove it with an **A/B** (`"memory": false` → it forgets), and inspect the **extracted** facts.

## Cleanup (avoid ongoing charges)

```bash
agentcore remove agent  --name cos       # remove the runtime from config
agentcore remove memory --name CosMemory # remove the memory from config
agentcore deploy -y                      # apply removals → destroys both
```

## What's deployed

- **Runtime**: the `cos` agent (BYO Container, HTTP). Execution IAM role auto-created by the CDK.
- **Memory**: `CosMemory` with two long-term strategies — `SEMANTIC` (`users/{actorId}/facts`) and
  `USER_PREFERENCE` (`users/{actorId}/preferences`) — `eventExpiryDuration: 7` to cap storage cost. The
  CDK **auto-grants** the runtime the memory data-plane actions and injects `MEMORY_COSMEMORY_ID`.
- **Graceful fallback**: if the memory id isn't present (e.g. local dev), the agent runs **stateless**
  exactly like Module 2 — never crashes.

## Notes
- `agentcore/aws-targets.json` (your account ID) and `.env` are **gitignored**. Commit only `.example`s.
- Reuses Module 1's agent bundle; `agent.py` is kept byte-identical (drift-guard test).
- The demo's recalled value (`$42.5M`) is **invented in-session on purpose** — it is *not* in the bundle's
  `CLAUDE.md` (which has a $30M figure), so recalling it can only be memory, not always-on context.
