"""Weather MCP server — exposes get_current_weather and get_forecast tools."""

from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic_settings import BaseSettings, CliApp

from app.weather import get_provider, resolve_location

mcp = FastMCP("weather")


@mcp.tool()
async def get_current_weather(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    """Get the current weather conditions for a location.

    Args:
        location: City or place name (e.g. "London" or "New York").
        lat: Latitude in decimal degrees. Must be combined with lon.
        lon: Longitude in decimal degrees. Must be combined with lat.

    Returns a dict with keys: temp_celsius, feels_like_celsius,
    humidity_percent, wind_speed_kmh, weather_code, description.
    """
    coords = await resolve_location(location, lat, lon)
    provider = get_provider()
    result = await provider.get_current(*coords)
    return result.model_dump()


@mcp.tool()
async def get_forecast(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    days: int = 7,
) -> dict:
    """Get a multi-day weather forecast for a location.

    Args:
        location: City or place name (e.g. "Tokyo" or "Berlin").
        lat: Latitude in decimal degrees. Must be combined with lon.
        lon: Longitude in decimal degrees. Must be combined with lat.
        days: Number of forecast days (1-16 for Open-Meteo, capped at 5
              for OpenWeatherMap free tier). Defaults to 7.

    Returns a dict with key "days", a list of daily dicts containing:
    date, temp_max_celsius, temp_min_celsius, precipitation_mm,
    weather_code, description.
    """
    coords = await resolve_location(location, lat, lon)
    provider = get_provider()
    result = await provider.get_forecast(*coords, days)
    return result.model_dump()


class ServerSettings(BaseSettings):
    """CLI and environment configuration for the weather MCP server."""

    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000

    def cli_cmd(self) -> None:
        if self.transport != "stdio":
            mcp.settings.host = self.host
            mcp.settings.port = self.port
        mcp.run(transport=self.transport)


if __name__ == "__main__":
    CliApp.run(ServerSettings)
