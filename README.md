# weather-mcp

An MCP (Model Context Protocol) server that exposes live weather tools for AI assistants. Supports current conditions and multi-day forecasts via [Open-Meteo](https://open-meteo.com/) (default, no API key) or [OpenWeatherMap](https://openweathermap.org/) (set `OPENWEATHERMAP_API_KEY`).

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.13+ | Manage with [pyenv](https://github.com/pyenv/pyenv) or system install |
| [uv](https://docs.astral.sh/uv/) | latest | Dependency management & virtualenv |

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/Filaton/weather-mcp.git
cd weather-mcp

# 2. Install all dependencies
uv sync

# 3. Install pre-commit hooks
uv run pre-commit install
```

## Running the Server

```bash
# stdio (default — for Claude Code / MCP clients that spawn the process)
uv run python main.py

# SSE over HTTP (for Docker or remote access)
uv run python main.py --transport sse
uv run python main.py --transport sse --host 127.0.0.1 --port 9000

# Streamable HTTP
uv run python main.py --transport streamable-http --port 9000
```

Transport and host/port can also be set via environment variables (`TRANSPORT`, `HOST`, `PORT`) — CLI args take priority.

## MCP Tools

### `get_current_weather`
Returns current conditions for a location.

| Parameter | Type | Description |
|---|---|---|
| `location` | `str` (optional) | City or place name, e.g. `"London"` |
| `lat` | `float` (optional) | Latitude — use with `lon` instead of `location` |
| `lon` | `float` (optional) | Longitude — use with `lat` instead of `location` |

Returns: `temp_celsius`, `feels_like_celsius`, `humidity_percent`, `wind_speed_kmh`, `weather_code`, `description`.

### `get_forecast`
Returns a multi-day forecast.

| Parameter | Type | Description |
|---|---|---|
| `location` | `str` (optional) | City or place name |
| `lat` | `float` (optional) | Latitude |
| `lon` | `float` (optional) | Longitude |
| `days` | `int` | Forecast days — 1–16 (Open-Meteo) or 1–5 (OpenWeatherMap). Default: 7 |

Returns: `days` list, each with `date`, `temp_max_celsius`, `temp_min_celsius`, `precipitation_mm`, `weather_code`, `description`.

## Weather Providers

| Provider | API key required | Max forecast days |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | No (default) | 16 |
| [OpenWeatherMap](https://openweathermap.org/) | Yes — set `OPENWEATHERMAP_API_KEY` | 5 |

The server selects the provider automatically: Open-Meteo is used unless `OPENWEATHERMAP_API_KEY` is set in the environment.

## Connecting to Claude Code

```bash
# Register globally (stdio)
claude mcp add weather -- uv run python /path/to/weather-mcp/main.py

# Register with SSE transport (e.g. Docker or remote server)
claude mcp add weather --transport sse http://localhost:8000/sse
```

## Running Tests

```bash
uv run pytest
uv run pytest --cov=app
```

## Code Quality

```bash
uv run ruff format .            # Format
uv run ruff check --fix .       # Lint and auto-fix
uv run pre-commit run --all-files  # All hooks
```

## Project Structure

```
.
├── main.py              # Server entry point (CLI via pydantic-settings CliApp)
├── app/
│   ├── schemas.py       # Pydantic models: API response validation + output types
│   └── weather.py       # Weather providers (Open-Meteo, OpenWeatherMap) + geocoding
├── tests/
│   └── test_main.py     # Pytest suite (17 tests)
├── pyproject.toml
└── pyrightconfig.json
```

