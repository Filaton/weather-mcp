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
uv run python main.py          # Run the MCP server (stdio, default)
uv run python main.py --help   # Show all CLI options
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

Dev dependencies (`pre-commit`, `pytest`, `pytest-asyncio`, `ruff`) are under `[dependency-groups] dev` in `pyproject.toml`.

## Architecture

- `main.py` (root) — Server entry point. CLI powered by `pydantic-settings` `CliApp`. Registers MCP tools and calls `mcp.run()`.
- `app/weather.py` — All weather logic: geocoding, `OpenMeteoProvider`, `OpenWeatherMapProvider`, `WeatherProvider` Protocol, `get_provider()` factory.
- `app/schemas.py` — Pydantic v2 models in two groups:
  - Private `_`-prefixed models for validating raw HTTP API responses (`model_validate()`)
  - Public output models returned by providers: `CurrentWeather`, `Forecast`, `ForecastDay`
- `tests/test_main.py` — 17 async pytest tests covering geocoding, location resolution, both providers, the factory, and `ValidationError` paths.

### MCP Server Pattern

MCP tools are registered functions the AI can call. The `mcp` SDK uses a decorator-based pattern:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

@mcp.tool()
async def get_current_weather(location: str) -> dict:
    ...
```

Run the server with `mcp.run()`. Tools receive typed parameters and return JSON-serializable results (use `.model_dump()` on Pydantic output models).

### CLI / Transport

The server supports three transports selectable at startup:

```bash
uv run python main.py                          # stdio (default)
uv run python main.py --transport sse          # SSE over HTTP
uv run python main.py --transport streamable-http
uv run python main.py --transport sse --host 127.0.0.1 --port 9000
```

`TRANSPORT`, `HOST`, and `PORT` env vars work as lower-priority fallbacks to CLI args (handled by `pydantic-settings`).

### Weather Providers

- **Open-Meteo** (default) — free, no key, up to 16-day forecast.
- **OpenWeatherMap** — activated when `OPENWEATHERMAP_API_KEY` env var is set; free tier capped at 5-day forecast.
- Provider is selected by `get_provider()` in `app/weather.py`.
- Geocoding (city name → lat/lon) always uses the Open-Meteo geocoding API regardless of provider.

## Code Style

- **Formatter/linter**: ruff (line length 88, rules: `E`, `W`, `F`, `I`)
- **Python version**: 3.13+ — use modern syntax (`X | Y` unions, `match` statements)
- **Type checking**: Pyright in `standard` mode (via `pyrightconfig.json`); annotations encouraged but not required everywhere
