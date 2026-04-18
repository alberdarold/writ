"""MCP server implementation — agent-to-agent interface for Writ.

Exposes the Writ interview and compilation pipeline as MCP tools so another
agent (the client) can script the whole spec-creation flow:

  writ_interview_start()           -> session_id, first question
  writ_interview_answer(id, text)  -> next question OR completed spec
  writ_one_shot(description)       -> spec in a single call (bulk mode)
  writ_compile(spec, format)       -> compiled output
  writ_resolve_connectors(spec)    -> list of resolved connectors
  writ_list_connectors()           -> full catalog
  writ_list_compilers()            -> available formats
  writ_get_session(id)             -> introspect an in-progress session

Transport defaults to stdio (for Claude Desktop, Cursor, etc). HTTP/SSE
support is available via the underlying SDK when `transport='http'` is used.
"""

from __future__ import annotations

import json
from typing import Any

from writ_agents.compilers import COMPILERS, format_choices
from writ_agents.core.schema import PartialSpec, Spec
from writ_agents.core.step import interview_step
from writ_agents.mcp.store import SessionStore
from writ_agents.providers.anthropic import AnthropicProvider
from writ_agents.providers.base import LLMProvider
from writ_agents.resolver.catalog import CATALOG
from writ_agents.resolver.resolver import resolve_connectors

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "MCP support requires the `mcp` package. "
        "Install with: pip install 'writ-agents[mcp]'"
    ) from e


_ONE_SHOT_SYSTEM = """You are Writ's one-shot spec extractor. The caller will give you a FULL
description of the automated helper they want. Your job is to produce a single
complete JSON InterviewResponse with status='ready' and every field filled in.
Do not ask follow-up questions — infer sensible defaults for any gap (e.g.
guardrails always include 'Never act outside the described scope'; oversight
defaults to human_in_loop for anything sending messages or taking actions).
Output must match the InterviewResponse schema from the Writ interview prompt."""


def _make_provider(api_key: str | None = None) -> LLMProvider:
    return AnthropicProvider(api_key=api_key)


def build_server(
    provider_factory: Any = _make_provider,
) -> tuple[FastMCP, SessionStore]:
    """Build the FastMCP server. Factored for testing."""
    mcp = FastMCP("writ")
    store = SessionStore()
    _provider_holder: dict[str, LLMProvider] = {}

    def _get_provider() -> LLMProvider:
        # One provider per server. Tests pass a factory that returns the same
        # MockProvider anyway, so this only matters in production where each
        # AnthropicProvider opens its own httpx client.
        provider = _provider_holder.get("p")
        if provider is None:
            provider = provider_factory()
            _provider_holder["p"] = provider
        return provider

    @mcp.tool()
    async def writ_interview_start(
        initial_description: str | None = None,
    ) -> dict[str, Any]:
        """Begin a new Writ interview session.

        Args:
            initial_description: Optional opening blob — describe the agent you
                want in plain English. If omitted, Writ asks its own opener.

        Returns:
            {session_id, message, partial_spec, confidence, status}
        """
        session = store.create()
        provider = _get_provider()
        async with store.lock_for(session.session_id):
            result = await interview_step(
                session, provider, user_input=initial_description
            )
        return {
            "session_id": session.session_id,
            "message": result.message,
            "partial_spec": result.partial_spec.model_dump(exclude_none=True),
            "confidence": result.confidence,
            "status": result.status,
            "error": result.error,
        }

    @mcp.tool()
    async def writ_interview_answer(session_id: str, answer: str) -> dict[str, Any]:
        """Answer the next interview question in an ongoing session.

        Args:
            session_id: The id returned from writ_interview_start.
            answer: Free-form plain-English reply.

        Returns:
            {message, partial_spec, confidence, status, spec?}
            When status == 'ready', `spec` contains the completed Spec as
            a dict — pass it to writ_compile and writ_resolve_connectors.
        """
        session = store.require(session_id)
        provider = _get_provider()
        async with store.lock_for(session_id):
            result = await interview_step(session, provider, user_input=answer)
        payload: dict[str, Any] = {
            "message": result.message,
            "partial_spec": result.partial_spec.model_dump(exclude_none=True),
            "confidence": result.confidence,
            "status": result.status,
            "error": result.error,
        }
        if result.spec is not None:
            payload["spec"] = result.spec.model_dump()
        return payload

    @mcp.tool()
    async def writ_one_shot(
        description: str,
        target_runtime: str = "all",
    ) -> dict[str, Any]:
        """Produce a complete Spec from a single rich description.

        Agent-to-agent shortcut: skip the turn-by-turn interview entirely.
        The calling agent passes everything it knows in one blob.

        Args:
            description: Full plain-English description of the desired agent.
            target_runtime: claude | openai | gemini | all (default: all).

        Returns:
            {spec, confidence} — spec is a fully validated Writ Spec dict,
            or {error} on failure.
        """
        from writ_agents.core.session import InterviewSession

        provider = _get_provider()
        session = InterviewSession()
        prompt = (
            f"{description}\n\n"
            f"TARGET_RUNTIME: {target_runtime}\n"
            "Produce the complete spec in this single reply. Set status='ready'."
        )
        result = await interview_step(session, provider, user_input=prompt)
        # Up to two follow-up nudges if the LLM isn't ready yet.
        for _ in range(2):
            if result.status == "ready" or result.status == "error":
                break
            result = await interview_step(
                session,
                provider,
                user_input="Finalize the spec now with status='ready'.",
            )
        if result.spec is None:
            return {
                "error": result.error or "One-shot could not produce a complete spec.",
                "partial_spec": result.partial_spec.model_dump(exclude_none=True),
                "confidence": result.confidence,
            }
        return {
            "spec": result.spec.model_dump(),
            "confidence": result.confidence,
        }

    @mcp.tool()
    async def writ_compile(
        spec: dict[str, Any],
        format: str = "agents-md",
        connectors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Compile a Spec into a target format.

        Args:
            spec: A validated Writ Spec object (from writ_interview_answer or
                  writ_one_shot).
            format: One of agents-md | claude | openai | gemini | oas.
            connectors: Optional list of resolved connector dicts (from
                        writ_resolve_connectors). Pass [] to skip.

        Returns:
            {format, content, extension}
        """
        if format not in COMPILERS:
            return {
                "error": f"Unknown format '{format}'. Choose: {', '.join(format_choices())}"
            }
        validated_spec = Spec.model_validate(spec)
        resolved: list[Any] = []
        if connectors:
            from writ_agents.core.schema import ResolvedConnector

            resolved = [ResolvedConnector.model_validate(c) for c in connectors]
        compiler = COMPILERS[format]
        return {
            "format": format,
            "content": compiler.compile(validated_spec, resolved),
            "extension": compiler.file_extension,
        }

    @mcp.tool()
    async def writ_compile_all(
        spec: dict[str, Any],
        connectors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Compile a Spec into every supported format at once.

        Returns:
            {formats: {format_name: {content, extension}, ...}}
        """
        validated_spec = Spec.model_validate(spec)
        resolved: list[Any] = []
        if connectors:
            from writ_agents.core.schema import ResolvedConnector

            resolved = [ResolvedConnector.model_validate(c) for c in connectors]
        return {
            "formats": {
                fmt: {
                    "content": compiler.compile(validated_spec, resolved),
                    "extension": compiler.file_extension,
                }
                for fmt, compiler in COMPILERS.items()
            }
        }

    @mcp.tool()
    async def writ_resolve_connectors(spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve the spec's business terms to concrete connectors.

        Args:
            spec: A validated Writ Spec object.

        Returns:
            {connectors: [...]} — each entry has connector_id, name, source,
            icon, description, business_terms, mcp_url.
        """
        validated = Spec.model_validate(spec)
        provider = _get_provider()
        resolved = await resolve_connectors(validated, provider)
        return {"connectors": [c.model_dump() for c in resolved]}

    @mcp.tool()
    def writ_list_connectors() -> dict[str, Any]:
        """Return the full embedded connector catalog."""
        return {"catalog": [c.model_dump() for c in CATALOG]}

    @mcp.tool()
    def writ_list_compilers() -> dict[str, Any]:
        """Return available output formats."""
        return {
            "formats": [
                {"name": fmt, "extension": compiler.file_extension}
                for fmt, compiler in COMPILERS.items()
            ]
        }

    @mcp.tool()
    def writ_get_session(session_id: str) -> dict[str, Any]:
        """Inspect an in-progress session."""
        session = store.get(session_id)
        if session is None:
            return {"error": f"No session '{session_id}'"}
        return {
            "session_id": session.session_id,
            "status": session.status,
            "turns": session.turns(),
            "partial_spec": session.accumulated.model_dump(exclude_none=True),
            "confidence": session.confidence,
            "spec": session.spec.model_dump() if session.spec else None,
            "error": session.error,
        }

    @mcp.tool()
    def writ_end_session(session_id: str) -> dict[str, Any]:
        """Discard a session and free its memory."""
        ok = store.delete(session_id)
        return {"deleted": ok}

    @mcp.resource("writ://catalog")
    def catalog_resource() -> str:
        """Full connector catalog as JSON."""
        return json.dumps([c.model_dump() for c in CATALOG], indent=2)

    @mcp.resource("writ://schema")
    def schema_resource() -> str:
        """JSON schema of a Spec + PartialSpec."""
        return json.dumps(
            {
                "Spec": Spec.model_json_schema(),
                "PartialSpec": PartialSpec.model_json_schema(),
            },
            indent=2,
        )

    return mcp, store


def serve(transport: str = "stdio") -> None:
    """Run the MCP server until the transport closes."""
    mcp, _ = build_server()
    if transport == "stdio":
        mcp.run()
    elif transport in ("sse", "http"):
        mcp.run(transport="sse")
    else:
        raise ValueError(f"Unknown transport: {transport!r}. Use 'stdio' or 'http'.")
