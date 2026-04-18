"""OpenAI Responses API agent compiler."""

from __future__ import annotations

import json
import re

from writ_agents.core.schema import ResolvedConnector, Spec


def _to_kebab(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class OpenAICompiler:
    format_name = "openai"
    file_extension = ".json"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        mcp_servers = [
            {
                "type": "url",
                "server_label": c.name.lower().replace(" ", "_"),
                "server_url": c.mcp_url,
            }
            for c in connectors
            if c.mcp_url
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": _to_kebab(tool),
                    "description": tool,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
            for tool in spec.tools_needed
        ]
        output = {
            "name": _to_kebab(spec.name),
            "model": "gpt-5",
            "instructions": spec.system_prompt,
            "mcp_servers": mcp_servers,
            "tools": tools,
            "metadata": {
                "archetype": spec.archetype,
                "audience": spec.audience,
            },
        }
        return json.dumps(output, indent=2)
