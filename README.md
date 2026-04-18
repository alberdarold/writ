# Writ

**Give your agent a writ.**

Writ turns plain business-language descriptions into portable AI agent specifications — through a friendly 5-8 question interview, no technical knowledge required.

## What it does

You answer questions like:
- "What repetitive task should this helper take over?"
- "Who will use it — customers, your team, managers?"
- "What should it never do?"

Writ produces:
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

That's it. The TUI launches and guides you through the interview.

## CLI Commands

```bash
# Start a new interview (launches TUI)
writ
writ create

# Compile an existing spec to a format
writ compile spec.json --to agents-md
writ compile spec.json --to claude
writ compile spec.json --to openai
writ compile spec.json --to gemini
writ compile spec.json --to oas

# Resolve connectors for a spec
writ resolve spec.json

# Show version
writ version
```

## Example Output

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
User answers → Interview loop (Claude) → PartialSpec accumulated
                                              ↓
                                        Connector resolution
                                              ↓
                                    5 compiled output formats
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

## Requirements

- Python 3.11+
- Anthropic API key

## License

MIT. See [LICENSE](LICENSE).
