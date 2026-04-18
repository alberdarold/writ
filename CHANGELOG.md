# Changelog

All notable changes to writ-agents will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
