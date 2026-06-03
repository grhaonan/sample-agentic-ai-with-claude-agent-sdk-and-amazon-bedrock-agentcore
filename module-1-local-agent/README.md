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

## Notes

- The model is selected via `ANTHROPIC_MODEL` (with `CLAUDE_CODE_USE_BEDROCK=1`) — there is **no
  hardcoded `model=`** in the code, so you can switch models from `.env` alone.
- This module needs **no Athena/S3**. The optional Text-to-SQL on Athena example lives under
  `advanced/text-to-sql-athena/`.
