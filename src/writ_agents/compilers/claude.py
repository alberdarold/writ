"""Claude (Anthropic Messages API) compiler."""

from __future__ import annotations

import json

from writ_agents.core.schema import ResolvedConnector, Spec


class ClaudeCompiler:
    format_name = "claude"
    file_extension = ".json"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        mcp_servers = [
            {
                "type": "url",
                "name": c.name.lower().replace(" ", "_"),
                "url": c.mcp_url,
            }
            for c in connectors
            if c.mcp_url
        ]
        output = {
            "model": "claude-opus-4-7",
            "system": spec.system_prompt,
            "mcp_servers": mcp_servers,
            "max_tokens": 4096,
            "metadata": {
                "agent_name": spec.name,
                "archetype": spec.archetype,
                "audience": spec.audience,
                "oversight": spec.oversight,
                "guardrails": spec.guardrails,
            },
        }
        return json.dumps(output, indent=2)
