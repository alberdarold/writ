"""Entry point for the writ CLI."""

from writ_agents.cli.commands import app


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
