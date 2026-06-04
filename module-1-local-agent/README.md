# Module 1 — Build a Local Agent

The first rung of the ladder: build an agent **on your own machine** with the
[Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview), running on
**Amazon Bedrock** for the model. No databases, no buckets — just AWS credentials and Bedrock access.

The running example is a **Chief of Staff** agent for a fictional 50-person startup, *TechStart Inc*.
You'll ask it about runway, burn rate, and hiring, and watch it grow from a one-line prototype into a
context-rich assistant.

## What you'll build (in one notebook)

`module-1-local-agent.ipynb`, in three parts:

- **Part 1A — The one-liner (`query()`).** A working agent loop in a handful of lines. Stateless: each call forgets the last.
- **Part 1B — The real agent (`ClaudeSDKClient` + context).** The same agent, upgraded with a **system prompt**, **`CLAUDE.md`** memory, a custom **skill**, and **multi-turn** conversation — then a tour of the full SDK feature set (Bash-run scripts, output styles, plan mode, slash commands, hooks, subagents).
- **Putting it all together.** Run the packaged `chief_of_staff_agent/agent.py` entrypoint end-to-end — the same entrypoint Module 2 will deploy.

## The agent lives on disk

The agent's *body* is the `chief_of_staff_agent/` folder — the SDK reads it from the filesystem
(via `cwd` + `setting_sources=["project"]`):

```
chief_of_staff_agent/
├── agent.py                 # the packaged entrypoint: send_query()
├── CLAUDE.md                # always-on company context (the "memory")
├── .claude/
│   ├── skills/financial-analysis/SKILL.md   # procedural domain expertise (loaded on demand)
│   ├── agents/              # subagents: financial-analyst, recruiter (Task delegation)
│   ├── commands/            # slash commands: /budget-impact, /strategic-brief, /talent-scan
│   ├── hooks/               # PostToolUse hooks → audit logs
│   ├── output-styles/       # executive / technical voices
│   └── settings.local.json  # wires up the hooks
├── scripts/                 # Python tools the agent runs via Bash
└── financial_data/          # burn rate, revenue forecast, hiring costs
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **Claude Code CLI** installed — the Agent SDK shells out to it
- **AWS credentials** configured (`aws sts get-caller-identity` should work)
- **Amazon Bedrock model access** enabled for the Claude models in `.env`

## Setup

First, install **uv** if you don't already have it (`uv --version` to check):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or, with Homebrew
brew install uv
```

Then, from this folder:

```bash
cd module-1-local-agent

# Install dependencies into a local .venv
uv sync

# Configure environment (Bedrock)
cp .env.example .env        # edit AWS_REGION / model IDs if needed

# Register the kernel, then open the notebook
uv run python -m ipykernel install --user --name module-1-local-agent
```

Open `module-1-local-agent.ipynb` and select the **module-1-local-agent** kernel.

You can also run the packaged agent directly from the command line:

```bash
uv run python -c "import anyio; from chief_of_staff_agent.agent import send_query; \
  anyio.run(lambda: send_query('What is our current runway?'))"
```

## Testing

A `pytest` suite in `tests/` keeps the notebook honest after edits. It has two tiers:

```bash
# FAST (no AWS credentials, ~seconds): notebook hygiene, agent config/skill/hook wiring,
# the scripts, and the audit hooks.
uv run --group test pytest

# SLOW (needs AWS credentials, ~minutes + real Bedrock tokens): executes the entire
# notebook end-to-end and asserts behavior (tools fired, report written, grounded facts).
uv run --group test pytest -m slow
```

Notes:
- The slow tier **auto-skips** when AWS credentials aren't available, so a bare `pytest` always runs clean.
- Assertions are **structural/behavioral**, not exact text — agent output is non-deterministic.
- The slow run **backs up and restores** `chief_of_staff_agent/audit/` and `output_reports/`, so it
  leaves the working tree clean.

Typical workflow after editing the notebook: run the fast tier for an instant regression check, then
run `-m slow` when you want a full behavioral pass.

## Notes

- The model is selected via `ANTHROPIC_MODEL` (with `CLAUDE_CODE_USE_BEDROCK=1`) — there is **no
  hardcoded `model=`** in the code, so you can switch models from `.env` alone.
- This module needs **no Athena/S3**. The optional Text-to-SQL on Athena example lives under
  `advanced/text-to-sql-athena/`.
