# Writ

**Give your agent a writ.**

Writ turns plain business-language descriptions into portable AI agent specifications — through a friendly interview (for humans) or an **MCP server** (for other agents). No technical knowledge required.

## What it does

Three ways to use it:

1. **Interactive TUI** — a non-technical user runs `writ`, answers 5–8 questions, and gets compiled specs.
2. **CLI** — `writ compile`, `writ bundle`, `writ resolve` operate on saved specs.
3. **MCP server** — `writ mcp-serve` exposes the whole pipeline to another agent. Agent-to-agent spec authoring.

Writ produces, from any of those three entry points:

- **AGENTS.md** — human-readable spec (agentskills.io format)
- **claude.json** — ready for Anthropic Messages API
- **openai.json** — ready for OpenAI Responses API
- **gemini.json** — ready for Google Gemini API
- **oas.yaml** — Open Agent Spec v1

## Quickstart

```bash
pip install writ-agents
export ANTHROPIC_API_KEY=sk-ant-...
writ
```

That's it — the TUI launches and guides you through the interview.

## CLI

```bash
writ                                      # start an interview
writ create                                # same as `writ`
writ compile spec.json --to claude -o out.json
writ compile spec.json --to agents-md --resolve -o AGENTS.md
writ bundle  spec.json -o ./dist --resolve           # emit all 5 formats
writ resolve spec.json                                # list matched connectors
writ doctor                                           # env/config diagnostics
writ config  --set-key sk-ant-...                     # save API key
writ mcp-serve                                        # run as an MCP server
writ version
```

## MCP server — agent-to-agent mode

Writ runs as an MCP server so other agents can build specs without a human in the loop:

```bash
writ mcp-serve              # stdio transport (default — for Claude Desktop, Cursor, etc.)
writ mcp-serve --transport http
```

Exposed tools:

| Tool | Purpose |
|------|---------|
| `writ_interview_start(initial_description?)` | Open a session, get the first question |
| `writ_interview_answer(session_id, answer)` | Reply, get next question or final spec |
| `writ_one_shot(description)` | Skip the interview — one call, full spec |
| `writ_resolve_connectors(spec)` | Map business terms → connector catalog |
| `writ_compile(spec, format)` | Compile to a single target format |
| `writ_compile_all(spec)` | Compile to all 5 formats at once |
| `writ_list_connectors()` / `writ_list_compilers()` | Introspect what's available |
| `writ_get_session(id)` / `writ_end_session(id)` | Session lifecycle |

Resources: `writ://catalog` (connector catalog), `writ://schema` (Spec JSON schema).

Example Claude Desktop config:

```json
{
  "mcpServers": {
    "writ": {
      "command": "writ",
      "args": ["mcp-serve"],
      "env": { "ANTHROPIC_API_KEY": "sk-ant-..." }
    }
  }
}
```

See [examples/mcp_client.py](examples/mcp_client.py) for a scripted agent-to-agent flow.

## Example output

After a 6-question interview about a support triage agent, Writ produces:

```markdown
# Support Triage Bot
> I help you route customer issues to the right team fast.

**Archetype:** triage

## Purpose
Automatically classify and route incoming customer support tickets.

## System Prompt
```
You are a support triage assistant. When a support email arrives,
classify it by urgency (high/medium/low) and department (billing,
technical, general). Route high-urgency tickets to the on-call
lead via Slack immediately. Never close a ticket without human review.
```
```

## Architecture

```
 Human via TUI ─┐
 CLI commands ──┼─► interview_step (core/step.py) ──► PartialSpec accumulated
 MCP server   ──┘                                               │
                                                                ▼
                                                        Connector resolution
                                                                │
                                                                ▼
                                                    5 compiled output formats
```

Every caller (TUI, CLI, MCP) sits on the same `interview_step` primitive in `core/step.py`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

## Requirements

- Python 3.11+
- Anthropic API key

## License

MIT. See [LICENSE](LICENSE).
