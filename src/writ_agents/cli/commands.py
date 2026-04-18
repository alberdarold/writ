"""Typer CLI commands for Writ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from writ_agents import __version__
from writ_agents.core.prompt import PROMPT_VERSION
from writ_agents.core.schema import Spec

app = typer.Typer(
    name="writ",
    help="Translate business descriptions into portable AI agent specifications.",
    no_args_is_help=False,
    invoke_without_command=True,
)

FORMAT_CHOICES = ["agents-md", "claude", "openai", "gemini", "oas"]


def _get_compilers() -> dict[str, object]:
    from writ_agents.compilers.agents_md import AgentsMdCompiler
    from writ_agents.compilers.claude import ClaudeCompiler
    from writ_agents.compilers.gemini import GeminiCompiler
    from writ_agents.compilers.oas import OASCompiler
    from writ_agents.compilers.openai import OpenAICompiler

    return {
        "agents-md": AgentsMdCompiler(),
        "claude": ClaudeCompiler(),
        "openai": OpenAICompiler(),
        "gemini": GeminiCompiler(),
        "oas": OASCompiler(),
    }


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Default command — start the interactive interview."""
    if ctx.invoked_subcommand is None:
        create()


@app.command()
def create() -> None:
    """Start the interactive agent interview (launches Textual UI)."""
    from writ_agents.cli.app import WritApp

    app_instance = WritApp()
    app_instance.run()


@app.command()
def compile(
    spec_file: Annotated[Path, typer.Argument(help="Path to a spec JSON file")],
    to: Annotated[
        str,
        typer.Option(help=f"Output format: {', '.join(FORMAT_CHOICES)}"),
    ] = "agents-md",
) -> None:
    """Compile an existing spec file to a specific format."""
    if to not in FORMAT_CHOICES:
        typer.echo(
            f"Unknown format '{to}'. Choose from: {', '.join(FORMAT_CHOICES)}", err=True
        )
        raise typer.Exit(1)
    if not spec_file.exists():
        typer.echo(f"File not found: {spec_file}", err=True)
        raise typer.Exit(1)
    raw = json.loads(spec_file.read_text())
    spec = Spec.model_validate(raw)
    compilers = _get_compilers()
    compiler = compilers[to]
    # All compilers implement .compile(spec, connectors)
    from writ_agents.compilers.agents_md import AgentsMdCompiler
    from writ_agents.compilers.claude import ClaudeCompiler
    from writ_agents.compilers.gemini import GeminiCompiler
    from writ_agents.compilers.oas import OASCompiler
    from writ_agents.compilers.openai import OpenAICompiler

    assert isinstance(
        compiler,
        (AgentsMdCompiler, ClaudeCompiler, OpenAICompiler, GeminiCompiler, OASCompiler),
    )
    typer.echo(compiler.compile(spec, []))


@app.command()
def resolve(
    spec_file: Annotated[Path, typer.Argument(help="Path to a spec JSON file")],
) -> None:
    """Show resolved connectors for a spec."""
    import asyncio

    from writ_agents.cli.config import get_api_key
    from writ_agents.providers.anthropic import AnthropicProvider
    from writ_agents.resolver.resolver import resolve_connectors

    key = get_api_key()
    if not key:
        typer.echo(
            "No API key found. Set ANTHROPIC_API_KEY or run 'writ create' first.",
            err=True,
        )
        raise typer.Exit(1)

    raw = json.loads(spec_file.read_text())
    spec = Spec.model_validate(raw)
    provider = AnthropicProvider(api_key=key)
    connectors = asyncio.run(resolve_connectors(spec, provider))

    typer.echo(f"\nResolved {len(connectors)} connector(s) for '{spec.name}':\n")
    for c in connectors:
        badge = f"[{c.source.upper()}]"
        typer.echo(f"  {c.icon} {c.name} {badge}")
        typer.echo(f"     {c.description}")
        typer.echo(f"     Matched from: {', '.join(c.business_terms)}")
        typer.echo()


@app.command()
def version() -> None:
    """Print version and prompt version."""
    typer.echo(f"writ {__version__} (prompt v{PROMPT_VERSION})")
