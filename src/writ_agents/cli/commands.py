"""Typer CLI commands for Writ."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from writ_agents import __version__
from writ_agents.compilers import COMPILERS, format_choices
from writ_agents.core.prompt import PROMPT_VERSION
from writ_agents.core.schema import ResolvedConnector, Spec

app = typer.Typer(
    name="writ",
    help="Translate business descriptions into portable AI agent specifications.",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Default command — start the interactive interview."""
    if ctx.invoked_subcommand is None:
        create()


@app.command()
def create() -> None:
    """Start the interactive agent interview (launches Textual UI)."""
    from writ_agents.cli.app import WritApp

    WritApp().run()


def _load_spec(spec_file: Path) -> Spec:
    if not spec_file.exists():
        typer.echo(f"File not found: {spec_file}", err=True)
        raise typer.Exit(1)
    return Spec.model_validate(json.loads(spec_file.read_text()))


async def _resolve(spec: Spec) -> list[ResolvedConnector]:
    from writ_agents.cli.config import get_api_key
    from writ_agents.providers.anthropic import AnthropicProvider
    from writ_agents.resolver.resolver import resolve_connectors

    key = get_api_key()
    if not key:
        typer.echo(
            "No API key found. Set ANTHROPIC_API_KEY or run 'writ config set-key'.",
            err=True,
        )
        raise typer.Exit(1)
    provider = AnthropicProvider(api_key=key)
    return await resolve_connectors(spec, provider)


@app.command()
def compile(
    spec_file: Annotated[Path, typer.Argument(help="Path to a spec JSON file")],
    to: Annotated[
        str, typer.Option(help=f"Output format: {', '.join(format_choices())}")
    ] = "agents-md",
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Write output to this path instead of stdout"),
    ] = None,
    resolve: Annotated[
        bool,
        typer.Option(
            "--resolve/--no-resolve",
            help="Resolve connectors via the LLM before compiling (requires API key)",
        ),
    ] = False,
) -> None:
    """Compile a spec JSON file to a target format."""
    if to not in COMPILERS:
        typer.echo(
            f"Unknown format '{to}'. Choose from: {', '.join(format_choices())}",
            err=True,
        )
        raise typer.Exit(1)

    spec = _load_spec(spec_file)
    connectors: list[ResolvedConnector] = []
    if resolve:
        connectors = asyncio.run(_resolve(spec))

    compiler = COMPILERS[to]
    content = compiler.compile(spec, connectors)

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        typer.echo(f"Wrote {out}")
    else:
        typer.echo(content)


@app.command()
def bundle(
    spec_file: Annotated[Path, typer.Argument(help="Path to a spec JSON file")],
    out_dir: Annotated[
        Path, typer.Option("--out", "-o", help="Output directory")
    ] = Path("writ_bundle"),
    resolve: Annotated[
        bool,
        typer.Option("--resolve/--no-resolve", help="Resolve connectors via the LLM"),
    ] = True,
) -> None:
    """Compile a spec to all supported formats at once."""
    spec = _load_spec(spec_file)
    connectors: list[ResolvedConnector] = []
    if resolve:
        connectors = asyncio.run(_resolve(spec))

    out_dir.mkdir(parents=True, exist_ok=True)
    for fmt, compiler in COMPILERS.items():
        path = out_dir / f"{fmt}{compiler.file_extension}"
        path.write_text(compiler.compile(spec, connectors), encoding="utf-8")
        typer.echo(f"  wrote {path}")
    typer.echo(f"\nBundle complete in {out_dir}")


@app.command()
def resolve(
    spec_file: Annotated[Path, typer.Argument(help="Path to a spec JSON file")],
) -> None:
    """Show resolved connectors for a spec."""
    spec = _load_spec(spec_file)
    connectors = asyncio.run(_resolve(spec))

    typer.echo(f"\nResolved {len(connectors)} connector(s) for '{spec.name}':\n")
    for c in connectors:
        typer.echo(f"  {c.icon} {c.name} [{c.source.upper()}]")
        typer.echo(f"     {c.description}")
        typer.echo(f"     Matched from: {', '.join(c.business_terms)}")
        typer.echo()


@app.command()
def doctor() -> None:
    """Print environment and configuration diagnostics."""
    import sys

    from writ_agents.cli.config import CONFIG_FILE, get_api_key
    from writ_agents.resolver.catalog import CATALOG

    typer.echo(f"writ:           {__version__}")
    typer.echo(f"prompt:         v{PROMPT_VERSION}")
    typer.echo(f"python:         {sys.version.split()[0]}")
    typer.echo(
        f"config file:    {CONFIG_FILE} ({'present' if CONFIG_FILE.exists() else 'missing'})"
    )
    key = get_api_key()
    typer.echo(f"api key:        {'set' if key else 'NOT SET (set ANTHROPIC_API_KEY)'}")
    typer.echo(f"connectors:     {len(CATALOG)} in catalog")
    typer.echo(f"compilers:      {', '.join(format_choices())}")


@app.command(name="mcp-serve")
def mcp_serve(
    transport: Annotated[
        str, typer.Option(help="Transport: stdio (default) or http")
    ] = "stdio",
) -> None:
    """Run Writ as an MCP server for agent-to-agent interaction."""
    try:
        from writ_agents.mcp.server import serve
    except ImportError as e:
        typer.echo(
            f"MCP support not installed: {e}\n"
            "Install with: pip install 'writ-agents[mcp]'",
            err=True,
        )
        raise typer.Exit(1) from e
    serve(transport=transport)


@app.command()
def config(
    set_key: Annotated[
        str | None, typer.Option("--set-key", help="Store an Anthropic API key")
    ] = None,
) -> None:
    """Inspect or update Writ configuration."""
    from writ_agents.cli.config import CONFIG_FILE, get_api_key, save_api_key

    if set_key:
        save_api_key(set_key)
        typer.echo(f"Saved API key to {CONFIG_FILE}")
        return

    key = get_api_key()
    typer.echo(f"config file: {CONFIG_FILE}")
    typer.echo(f"api key:     {'configured' if key else 'not set'}")


@app.command()
def version() -> None:
    """Print version and prompt version."""
    typer.echo(f"writ {__version__} (prompt v{PROMPT_VERSION})")
