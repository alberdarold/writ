# Contributing to Writ

## Dev Setup

```bash
# Clone the repo
git clone https://github.com/alberdarold/writ.git
cd writ

# Install uv (if not installed)
pip install uv

# Install all dev dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

## Running Tests

```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --tb=short -v
```

## Linting and Formatting

```bash
# Fix lint issues automatically
uv run ruff check . --fix

# Format
uv run ruff format .

# Type check
uv run mypy --strict src
```

## Adding a Compiler

1. Create `src/writ_agents/compilers/my_format.py`
2. Implement the `Compiler` protocol (see `docs/COMPILERS.md`)
3. Add tests in `tests/compilers/test_my_format.py`
4. Register in the CLI's `_get_compilers()` in `cli/commands.py`
5. Add to `RevealScreen.COMPILERS` in `cli/screens/reveal.py`

## Submitting a PR

1. Branch from `main`
2. Make your changes
3. Ensure `uv run pytest` passes
4. Ensure `uv run ruff check .` passes
5. Ensure `uv run mypy --strict src` passes
6. Open a PR with a clear description of what and why
