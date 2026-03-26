"""Weather providers and location utilities for the MCP server."""

import os
from typing import Protocol, runtime_checkable

import httpx

# WMO Weather Interpretation Codes (used by Open-Meteo)
WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


async def geocode(location: str) -> tuple[float, float]:
    """Resolve a city/place name to (latitude, longitude).

    Raises ValueError if the location cannot be found.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params={"name": location, "count": 1})
        response.raise_for_status()
        data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Location not found: {location!r}")

    result = results[0]
    return float(result["latitude"]), float(result["longitude"])


async def resolve_location(
    location: str | None,
    lat: float | None,
    lon: float | None,
) -> tuple[float, float]:
    """Return (latitude, longitude) from whichever inputs are provided.

    Priority: explicit lat/lon > city name string.
    Raises ValueError if neither is provided or geocoding fails.
    """
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    if location:
        return await geocode(location)
    raise ValueError("Provide either a location name or both lat and lon.")


@runtime_checkable
class WeatherProvider(Protocol):
    async def get_current(self, lat: float, lon: float) -> dict:
        """Return current weather conditions as a normalized dict."""
        ...

    async def get_forecast(self, lat: float, lon: float, days: int) -> dict:
        """Return a multi-day forecast as a normalized dict."""
        ...


class OpenMeteoProvider:
    """Fetches weather from Open-Meteo (free, no API key required)."""

    _BASE = "https://api.open-meteo.com/v1/forecast"

    async def get_current(self, lat: float, lon: float) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "wind_speed_10m",
                "weather_code",
            ],
            "wind_speed_unit": "kmh",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self._BASE, params=params)
            response.raise_for_status()
            data = response.json()

        c = data["current"]
        code = int(c["weather_code"])
        return {
            "temp_celsius": c["temperature_2m"],
            "feels_like_celsius": c["apparent_temperature"],
            "humidity_percent": c["relative_humidity_2m"],
            "wind_speed_kmh": c["wind_speed_10m"],
            "weather_code": code,
            "description": WMO_DESCRIPTIONS.get(code, f"WMO code {code}"),
        }

    async def get_forecast(self, lat: float, lon: float, days: int) -> dict:
        days = min(max(days, 1), 16)
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "weather_code",
            ],
            "forecast_days": days,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self._BASE, params=params)
            response.raise_for_status()
            data = response.json()

        daily = data["daily"]
        result_days = []
        for i, date in enumerate(daily["time"]):
            code = int(daily["weather_code"][i])
            result_days.append(
                {
                    "date": date,
                    "temp_max_celsius": daily["temperature_2m_max"][i],
                    "temp_min_celsius": daily["temperature_2m_min"][i],
                    "precipitation_mm": daily["precipitation_sum"][i],
                    "weather_code": code,
                    "description": WMO_DESCRIPTIONS.get(code, f"WMO code {code}"),
                }
            )
        return {"days": result_days}


class OpenWeatherMapProvider:
    """Fetches weather from OpenWeatherMap (requires API key)."""

    _BASE = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def get_current(self, lat: float, lon: float) -> dict:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self._api_key,
            "units": "metric",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self._BASE}/weather", params=params)
            response.raise_for_status()
            data = response.json()

        return {
            "temp_celsius": data["main"]["temp"],
            "feels_like_celsius": data["main"]["feels_like"],
            "humidity_percent": data["main"]["humidity"],
            "wind_speed_kmh": round(data["wind"]["speed"] * 3.6, 1),
            "weather_code": data["weather"][0]["id"],
            "description": data["weather"][0]["description"].capitalize(),
        }

    async def get_forecast(self, lat: float, lon: float, days: int) -> dict:
        # OWM free tier: 5-day forecast in 3-hour steps
        days = min(max(days, 1), 5)
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self._api_key,
            "units": "metric",
            "cnt": days * 8,  # 8 × 3 h = 24 h per day
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self._BASE}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

        # Aggregate 3-hour slots into daily buckets
        buckets: dict[str, dict] = {}
        for entry in data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            if date not in buckets:
                buckets[date] = {
                    "temps": [],
                    "precip": 0.0,
                    "weather_id": entry["weather"][0]["id"],
                    "description": entry["weather"][0]["description"].capitalize(),
                }
            buckets[date]["temps"].append(entry["main"]["temp"])
            buckets[date]["precip"] += entry.get("rain", {}).get("3h", 0.0)
            buckets[date]["precip"] += entry.get("snow", {}).get("3h", 0.0)

        result_days = []
        for date, bucket in sorted(buckets.items()):
            result_days.append(
                {
                    "date": date,
                    "temp_max_celsius": round(max(bucket["temps"]), 1),
                    "temp_min_celsius": round(min(bucket["temps"]), 1),
                    "precipitation_mm": round(bucket["precip"], 1),
                    "weather_code": bucket["weather_id"],
                    "description": bucket["description"],
                }
            )
        return {"days": result_days}


def get_provider() -> WeatherProvider:
    """Return the appropriate provider based on available environment variables."""
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if api_key:
        return OpenWeatherMapProvider(api_key)
    return OpenMeteoProvider()
