# Changelog

All notable changes to writ-agents will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-04-18

### Added
- **MCP server** (`writ_agents.mcp`) — agent-to-agent interface exposing the full Writ pipeline as MCP tools. Launch with `writ mcp-serve` (stdio or http transport). Tools: `writ_interview_start`, `writ_interview_answer`, `writ_one_shot`, `writ_compile`, `writ_compile_all`, `writ_resolve_connectors`, `writ_list_connectors`, `writ_list_compilers`, `writ_get_session`, `writ_end_session`. Resources: `writ://catalog`, `writ://schema`.
- `InterviewSession` + `interview_step` in `core/` — stateless one-step driver that all callers (TUI, CLI, MCP) share.
- CLI: `writ bundle`, `writ doctor`, `writ config`, `--out` and `--resolve` on `writ compile`.
- TUI: confidence progress bar, connector resolution after interview completes, connectors included in reveal screen.
- Anthropic provider: prompt caching on the system block, exponential-backoff retry on rate-limit/connection errors, proper handling of non-text response blocks.
- Public API: top-level re-exports of `Spec`, `PartialSpec`, `InterviewSession`, `run_interview`, `interview_step`, and all compilers from `writ_agents`.
- Compiler registry (`writ_agents.compilers.COMPILERS`) — single source of truth shared by the CLI, TUI reveal, and MCP server.
- Tests: `tests/core/test_step.py`, `tests/core/test_confidence.py`, `tests/test_mcp_server.py` (+22 tests; total 67).

### Fixed
- **TUI concurrent-generator race** — `WritApp` now drives `interview_step` directly instead of racing `async for` with `asend`.
- **TUI never resolved connectors** — reveal screen now shows the resolved connector catalog.
- `_parse_response` handles fenced JSON with trailing prose via regex.
- `is_spec_complete` and `compute_confidence` now agree that an empty required list counts as missing.
- Anthropic provider no longer crashes when the response contains a non-text block.

## [0.1.0] - 2026-04-18

### Added
- Core interview loop (`core/interview.py`) — async generator driven by Anthropic Claude
- Pydantic data models: `PartialSpec`, `Spec`, `InterviewResponse`, `ResolvedConnector`, event types
- Merge logic for incremental spec accumulation (`core/merge.py`)
- Confidence scoring (`core/confidence.py`)
- Anthropic provider (`providers/anthropic.py`)
- Connector catalog with 19 entries (`resolver/catalog.py`)
- LLM-powered connector resolver (`resolver/resolver.py`)
- Five compilers: AGENTS.md, Claude JSON, OpenAI JSON, Gemini JSON, OAS YAML
- Textual TUI with chat panel, spec card, and reveal screen
- Typer CLI with `create`, `compile`, `resolve`, and `version` commands
- Full test suite (schema, merge, interview, all 5 compilers, resolver)
- Documentation: INTERVIEW_TAXONOMY.md, COMPILERS.md, ARCHITECTURE.md
- CI workflow for Python 3.11/3.12/3.13
- Pre-commit hooks (ruff + mypy)
