"""Open Agent Spec (YAML) compiler."""

from __future__ import annotations

from typing import Any

import yaml

from writ_agents.core.schema import ResolvedConnector, Spec


class OASCompiler:
    format_name = "oas"
    file_extension = ".yaml"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        data: dict[str, Any] = {
            "apiVersion": "openagentspec.dev/v1",
            "kind": "Agent",
            "metadata": {
                "name": spec.name,
                "description": spec.tagline,
                "version": spec.schema_version,
            },
            "spec": {
                "archetype": spec.archetype,
                "purpose": spec.purpose,
                "audience": spec.audience,
                "personality": spec.personality_traits,
                "systemPrompt": spec.system_prompt,
                "capabilities": {
                    "knowledgeSources": list(spec.knowledge_sources),
                    "tools": list(spec.tools_needed),
                },
                "connectors": [
                    {
                        "id": c.connector_id,
                        "name": c.name,
                        "source": c.source,
                        "url": c.mcp_url,
                    }
                    for c in connectors
                ],
                "guardrails": list(spec.guardrails),
                "oversight": spec.oversight,
                "targetRuntime": spec.target_runtime,
            },
        }
        result: str = yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        return result
