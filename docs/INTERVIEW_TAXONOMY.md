# Interview Taxonomy

This document describes every field Writ collects during an interview, why it matters, and how it maps to compiled outputs.

## Fields

### `name`
**What it is:** A short (2-4 word), human-readable name for the agent.
**Why it matters:** Used as the identifier in all compiled outputs and the bundle directory name.
**Compiled to:** Title in AGENTS.md, `name` in OpenAI JSON, `metadata.agentName` in Gemini, `metadata.name` in OAS.

### `archetype`
**What it is:** One of: `Q&A`, `research`, `triage`, `drafting`, `scheduling`, `monitoring`, `other`.
**Why it matters:** Sets expectations about the agent's primary mode of operation.
**Compiled to:** `**Archetype:**` line in AGENTS.md, `metadata.archetype` in Claude/OpenAI/Gemini, `spec.archetype` in OAS.

### `tagline`
**What it is:** A one-sentence first-person description ("I help you...").
**Why it matters:** The elevator pitch for the agent.
**Compiled to:** Subtitle in AGENTS.md, `metadata.description` in OAS.

### `purpose`
**What it is:** The concrete business problem this agent solves.
**Why it matters:** Drives the system prompt generation.
**Compiled to:** `## Purpose` section in AGENTS.md, `spec.purpose` in OAS.

### `audience`
**What it is:** Who will interact with this agent.
**Why it matters:** Shapes tone, vocabulary, and trust level in the system prompt.
**Compiled to:** `## Audience` in AGENTS.md, `spec.audience` in OAS.

### `knowledge_sources`
**What it is:** Plain-language list of information sources the agent reads from.
**Why it matters:** Maps to connector catalog entries; drives tool provisioning.
**Compiled to:** `### Knows about` in AGENTS.md; feeds connector resolution.

### `tools_needed`
**What it is:** Plain-language list of actions the agent can take.
**Why it matters:** Maps to connector catalog entries; becomes function declarations.
**Compiled to:** `### Can do` in AGENTS.md; `tools` array in OpenAI/Gemini; feeds connector resolution.

### `guardrails`
**What it is:** Things the agent must never do.
**Why it matters:** Critical for safe deployment; included verbatim in system prompts.
**Compiled to:** `## Guardrails` in AGENTS.md; `metadata.guardrails` in Claude; `spec.guardrails` in OAS.

### `oversight`
**What it is:** One of: `human_in_loop`, `sample_review`, `team_review`, `autonomous`.
**Why it matters:** Determines how actions are approved before execution.
**Compiled to:** `## Oversight` in AGENTS.md; `metadata.oversight` in Claude/Gemini; `spec.oversight` in OAS.

| Value | Meaning |
|-------|---------|
| `human_in_loop` | Every action requires human approval |
| `sample_review` | Random sample of actions reviewed |
| `team_review` | Actions reviewed by team periodically |
| `autonomous` | Agent acts without approval |

### `personality_traits`
**What it is:** 2-3 tone adjectives (e.g., friendly, concise, professional).
**Why it matters:** Shapes the system prompt's voice.
**Compiled to:** `## Personality` in AGENTS.md; `spec.personality` in OAS.

### `system_prompt`
**What it is:** Full natural-language instructions for the AI system.
**Why it matters:** The core artifact — everything else is metadata around this.
**Compiled to:** System prompt / instructions field in all formats.

### `target_runtime`
**What it is:** One of: `claude`, `openai`, `gemini`, `all`.
**Why it matters:** Hints which compiled format is primary; defaults to `all`.
**Compiled to:** `spec.targetRuntime` in OAS.

## Confidence Score

Confidence is a 0-100 integer reflecting how complete the spec picture is:

| Range | Interpretation |
|-------|----------------|
| 0-30 | General topic only |
| 31-60 | Purpose and audience known |
| 61-84 | Most fields set, some gaps |
| 85-100 | All fields set, ready to compile |

Field weights used in `compute_confidence()`:
- purpose: 15
- tools_needed: 15
- audience: 10
- knowledge_sources: 10
- guardrails: 10
- oversight: 10
- system_prompt: 10
- name: 5
- tagline: 5
- archetype: 5
- personality_traits: 5
