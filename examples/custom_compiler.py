"""Example showing how to write a custom compiler."""

from __future__ import annotations

from writ_agents.core.schema import ResolvedConnector, Spec


class LangGraphCompiler:
    """Example custom compiler targeting LangGraph."""

    format_name = "langgraph"
    file_extension = ".py"

    def compile(self, spec: Spec, connectors: list[ResolvedConnector]) -> str:
        """Generate a skeleton LangGraph agent from the spec."""
        lines = [
            '"""',
            f"LangGraph agent: {spec.name}",
            f"{spec.tagline}",
            '"""',
            "",
            "from __future__ import annotations",
            "from langgraph.graph import StateGraph, END",
            "from typing import TypedDict",
            "",
            "",
            "class AgentState(TypedDict):",
            "    messages: list[str]",
            "    context: dict",
            "",
            "",
            "# System prompt",
            f'SYSTEM_PROMPT = """{spec.system_prompt}"""',
            "",
            "",
            "def route(state: AgentState) -> str:",
            '    """Routing node."""',
            "    # TODO: implement routing logic",
            '    return "respond"',
            "",
            "",
            "def respond(state: AgentState) -> AgentState:",
            '    """Response node."""',
            "    # TODO: implement response logic using SYSTEM_PROMPT",
            "    return state",
            "",
            "",
            "# Build graph",
            "builder = StateGraph(AgentState)",
            'builder.add_node("route", route)',
            'builder.add_node("respond", respond)',
            'builder.set_entry_point("route")',
            'builder.add_edge("respond", END)',
            "graph = builder.compile()",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    # Demo: compile a minimal spec
    from writ_agents.core.schema import Spec

    spec = Spec(
        name="Demo Agent",
        archetype="Q&A",
        tagline="I help you answer questions.",
        purpose="Answer customer questions quickly.",
        audience="Customers",
        knowledge_sources=["FAQ database"],
        tools_needed=["search FAQ"],
        guardrails=["Never share pricing without manager approval"],
        oversight="sample_review",
        personality_traits=["friendly", "concise"],
        system_prompt="You are a helpful Q&A assistant. Answer questions based on the FAQ.",
        target_runtime="all",
    )

    compiler = LangGraphCompiler()
    print(compiler.compile(spec, []))
