# Architecture

## Module Map

```
writ_agents/
├── core/           — Schemas, InterviewSession, interview_step, merge, confidence
├── providers/      — LLM provider abstractions (Anthropic today)
├── resolver/       — Connector matching (catalog + LLM)
├── compilers/      — Spec-to-format compilers + registry
├── mcp/            — MCP server exposing tools for agent-to-agent use
└── cli/            — Typer CLI + Textual TUI
```

## Data Flow

Every caller — TUI, CLI, MCP server — drives the same primitive: `interview_step(session, provider, user_input)`. It's a plain async function that returns a `StepResult`. The async generator `run_interview` is a thin wrapper for push-driven consumers.

```
TUI / CLI / MCP tool
        │
        ▼
  interview_step()        ← core/step.py
  (pure function on a mutable InterviewSession)
        │
        ├─ calls LLMProvider.call()   ← providers/anthropic.py
        │  (Anthropic Claude, retries + prompt caching)
        │
        ├─ parses + merges response
        │
        └─ returns StepResult {message, partial_spec, confidence, status, spec?}
        │
        ▼
  PartialSpec (accumulated via merge_partial)
        │
        ▼
  Spec (promoted when all fields present)
        │
        ├─ resolve_connectors()    ← resolver/resolver.py
        │  (LLM maps business terms → catalog IDs)
        │
        └─ Compiler.compile()     ← compilers/*.py
           (5 output formats)
```

## Key Design Decisions

### Async Generator Protocol
The interview loop is an `AsyncGenerator[InterviewEvent, str | None]`. The TUI calls `asend(user_input)` to inject user responses. This keeps all state inside the generator and makes the loop testable without a real UI.

### PartialSpec vs Spec
`PartialSpec` has all fields optional — it accumulates incrementally. `Spec` requires all fields and validates them. `Spec.from_partial()` promotes a complete `PartialSpec` to a `Spec`.

### Merge Semantics
`merge_partial(base, update)` uses **replacement semantics for lists** — an updated list replaces the old one entirely. This matches LLM behavior: when the LLM re-states a list, it's providing the complete current state.

### Connector Resolution
Connectors are resolved in a second LLM call after the interview completes. The LLM maps plain-language terms to catalog IDs. Results are grouped by connector ID to deduplicate.

### Protocol-based Compilers
Compilers implement the `Compiler` protocol (structural subtyping). No inheritance required — duck typing works. This makes adding new compilers trivial.

## Extension Points

### Adding a new LLM provider
Implement the `LLMProvider` protocol in `providers/`:
```python
class MyProvider:
    async def call(self, conversation: list[dict[str, str]], system: str) -> str:
        ...
```

### Adding a new compiler
Implement the `Compiler` protocol in `compilers/`:
```python
class MyCompiler:
    format_name = "my-format"
    file_extension = ".txt"
    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        ...
```

### Adding connector catalog entries
Add a `ConnectorEntry` to the `CATALOG` list in `resolver/catalog.py`. Include rich `aliases` for better LLM matching.

### Adding interview fields
1. Add field to `PartialSpec` and `Spec` in `core/schema.py`
2. Update `INTERVIEW_SYSTEM_PROMPT` in `core/prompt.py`
3. Update `is_spec_complete()` in `core/merge.py`
4. Update `FIELD_WEIGHTS` in `core/confidence.py`
5. Update compilers as needed
