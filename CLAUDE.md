# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

An MCP (Model Context Protocol) server that exposes weather tools — live conditions and forecasts — for AI assistants to consume. Built with the `mcp` Python SDK (>=1.26.0).

## Setup

```bash
uv sync                        # Install all dependencies (use uv, never pip)
uv run pre-commit install      # Install git hooks
```

## Essential Commands

```bash
uv run python -m app.main      # Run the MCP server
uv run pytest                  # Run all tests
uv run pytest tests/test_foo.py::test_bar  # Run a single test
uv run pytest --cov=app        # Run tests with coverage
uv run ruff format .           # Format code
uv run ruff check --fix .      # Lint and auto-fix
uv run pre-commit run --all-files  # Run all pre-commit hooks manually
```

Pre-commit hooks fire automatically on `git commit`, running ruff lint + format on staged Python files.

## Dependency Management

Always use `uv`, never `pip`:

```bash
uv add <package>               # Add a runtime dependency
uv add --dev <package>         # Add a dev dependency
```

Dev dependencies (`pre-commit`, `pytest`, `ruff`) are under `[dependency-groups] dev` in `pyproject.toml`.

## Architecture

- `app/` — All application code lives here; run via `uv run python -m app.main`
- `tests/` — Pytest suite mirroring `app/` structure; add `tests/conftest.py` when shared fixtures are needed
- `main.py` (root) — Optional standalone entry point, separate from the `app` package

### MCP Server Pattern

MCP tools are registered functions the AI can call. The `mcp` SDK uses a decorator-based pattern:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

@mcp.tool()
def get_current_weather(location: str) -> dict:
    ...
```

Run the server with `mcp.run()`. Tools receive typed parameters and return JSON-serializable results.

## Code Style

- **Formatter/linter**: ruff (line length 88, rules: `E`, `W`, `F`, `I`)
- **Python version**: 3.13+ — use modern syntax (`X | Y` unions, `match` statements)
- **Type checking**: Pyright in `standard` mode (via `pyrightconfig.json`); annotations encouraged but not required everywhere
