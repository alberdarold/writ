# Compilers

Writ ships with 5 built-in compilers. Each transforms a `Spec` + resolved connectors into a target-specific string output.

## Built-in Compilers

| Compiler | Format | File | Target |
|----------|--------|------|--------|
| `AgentsMdCompiler` | Markdown | `AGENTS.md` | agentskills.io format |
| `ClaudeCompiler` | JSON | `claude.json` | Anthropic Messages API |
| `OpenAICompiler` | JSON | `openai.json` | OpenAI Responses API |
| `GeminiCompiler` | JSON | `gemini.json` | Google Gemini API |
| `OASCompiler` | YAML | `oas.yaml` | Open Agent Spec v1 |

## How to Write a Custom Compiler

A compiler is any class that implements the `Compiler` protocol:

```python
from writ_agents.compilers.base import Compiler
from writ_agents.core.schema import ResolvedConnector, Spec

class MyCompiler:
    format_name = "my-format"
    file_extension = ".txt"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        # Build your output string here
        return f"Agent: {spec.name}\n{spec.system_prompt}"
```

### Fields available on `Spec`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Agent name |
| `archetype` | `str` | Agent archetype |
| `tagline` | `str` | One-line description |
| `purpose` | `str` | Problem solved |
| `audience` | `str` | Target users |
| `knowledge_sources` | `list[str]` | Information sources |
| `tools_needed` | `list[str]` | Actions available |
| `guardrails` | `list[str]` | Things agent must not do |
| `oversight` | `str` | Oversight level |
| `personality_traits` | `list[str]` | Tone adjectives |
| `system_prompt` | `str` | Full system prompt |
| `target_runtime` | `str` | Target platform |
| `schema_version` | `str` | Schema version |

### Fields available on `ResolvedConnector`

| Field | Type | Description |
|-------|------|-------------|
| `connector_id` | `str` | Catalog ID |
| `name` | `str` | Display name |
| `source` | `str` | `mcp`, `oauth`, or `manual` |
| `icon` | `str` | Emoji icon |
| `description` | `str` | Short description |
| `business_terms` | `list[str]` | Matched business terms |
| `mcp_url` | `str | None` | MCP server URL if applicable |

## Testing Pattern

Use the shared `SPEC` and `CONNECTOR` fixtures from `tests/compilers/test_agents_md.py`:

```python
from tests.compilers.test_agents_md import SPEC, CONNECTOR
from my_package.my_compiler import MyCompiler

def test_my_compiler_outputs_name() -> None:
    compiler = MyCompiler()
    output = compiler.compile(SPEC, [CONNECTOR])
    assert "Support Triage Bot" in output
```

## Using the CLI with a Custom Compiler

Custom compilers are not yet integrated into the CLI. To use one programmatically:

```python
from my_package.my_compiler import MyCompiler
from writ_agents.core.schema import Spec
import json

spec = Spec.model_validate(json.loads(open("spec.json").read()))
compiler = MyCompiler()
print(compiler.compile(spec, []))
```
