"""Google Gemini compiler."""

from __future__ import annotations

import json
import re

from writ_agents.core.schema import ResolvedConnector, Spec


def _to_camel(s: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", "", s.lower()).split()
    return words[0] + "".join(w.capitalize() for w in words[1:]) if words else "action"


class GeminiCompiler:
    format_name = "gemini"
    file_extension = ".json"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        function_declarations = [
            {
                "name": _to_camel(tool),
                "description": tool,
                "parameters": {"type": "object", "properties": {}},
            }
            for tool in spec.tools_needed
        ]
        output = {
            "model": "gemini-2.5-pro",
            "systemInstruction": {"parts": [{"text": spec.system_prompt}]},
            "tools": [{"functionDeclarations": function_declarations}],
            "metadata": {
                "agentName": spec.name,
                "archetype": spec.archetype,
                "oversight": spec.oversight,
            },
        }
        return json.dumps(output, indent=2)
