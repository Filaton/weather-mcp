# Copilot Instructions

## Project Overview

An MCP (Model Context Protocol) server exposing weather tools (current conditions + multi-day forecast) for AI assistants. Entry point is `main.py` at the repo root. All weather and schema logic lives in `app/`.

## Key Structure

```
main.py          # Server entry point — CLI via pydantic-settings CliApp, registers MCP tools
app/
  schemas.py     # Pydantic v2 models: raw API response validation + normalized output types
  weather.py     # OpenMeteoProvider, OpenWeatherMapProvider, geocoding, get_provider() factory
  __init__.py
tests/
  test_main.py   # 17 async pytest tests
pyproject.toml   # Project metadata, dependencies, and all tool config
pyrightconfig.json
```

## Dependency Management — always use `uv`, never `pip`

```bash
uv sync                        # Install/sync all dependencies (including dev)
uv add <package>               # Add a runtime dependency
uv add --dev <package>         # Add a dev dependency
```

Runtime deps: `mcp`, `httpx`, `pydantic`, `pydantic-settings`.
Dev deps (`pre-commit`, `pytest`, `pytest-asyncio`, `ruff`) are under `[dependency-groups] dev` in [pyproject.toml](../pyproject.toml).

## Essential Commands

```bash
uv run python main.py           # Run the MCP server (stdio)
uv run python main.py --help    # Show transport/host/port options
uv run pytest                   # Run tests
uv run pytest --cov=app         # Run tests with coverage
uv run ruff format .            # Format code
uv run ruff check --fix .       # Lint and auto-fix
uv run pre-commit run --all-files  # Run all pre-commit hooks manually
```

Pre-commit hooks fire automatically on `git commit`, running ruff lint + format on staged Python files.

## Code Style & Conventions

- **Formatter / linter / import sorter**: ruff (replaces black, flake8, isort)
- **Line length**: 88 (configured in `[tool.ruff]` in [pyproject.toml](../pyproject.toml))
- **Active lint rule sets**: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort)
- **Python version**: 3.13+ — use modern syntax (e.g., `X | Y` unions, `match` statements)
- VS Code auto-formats and organizes imports on save via the Ruff extension

## Type Checking

Pyright runs in `standard` mode (see [pyrightconfig.json](../pyrightconfig.json)), using the `.venv` virtualenv. Annotations are encouraged but not required everywhere. Pylance in VS Code reflects the same configuration.

## Architecture Notes

- **Providers** (`app/weather.py`): `OpenMeteoProvider` is the default (no key); `OpenWeatherMapProvider` activates when `OPENWEATHERMAP_API_KEY` env var is set. Both implement the `WeatherProvider` Protocol and return typed Pydantic output models (`CurrentWeather`, `Forecast`).
- **Schemas** (`app/schemas.py`): two groups — private `_`-prefixed inbound models for `model_validate()` on raw HTTP responses, and public output models. Providers return output models; `main.py` calls `.model_dump()` before returning to MCP.
- **CLI**: `ServerSettings(BaseSettings)` with `transport`, `host`, `port` fields. `CliApp.run(ServerSettings)` handles arg parsing, choice validation, and env var fallback automatically. Transports: `stdio` (default), `sse`, `streamable-http`.
- **Geocoding**: city names are resolved to lat/lon via the Open-Meteo geocoding API regardless of which weather provider is active.
- **Tests**: all async, use `AsyncMock` + `patch` to mock `httpx.AsyncClient`. Include `ValidationError` tests for both providers.

## Adding Tests

Place test files under `tests/`. Pytest discovers them automatically (`testpaths = ["tests"]` in [pyproject.toml](../pyproject.toml)). `asyncio_mode = "auto"` is set so `async def test_*` functions work without decorators.
