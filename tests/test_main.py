"""Tests for the weather MCP server and its providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.weather import (
    OpenMeteoProvider,
    OpenWeatherMapProvider,
    geocode,
    get_provider,
    resolve_location,
)

# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------


async def test_geocode_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"latitude": 51.5074, "longitude": -0.1278}]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.weather.httpx.AsyncClient", return_value=mock_client):
        lat, lon = await geocode("London")

    assert lat == pytest.approx(51.5074)
    assert lon == pytest.approx(-0.1278)


async def test_geocode_not_found():
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.weather.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Location not found"):
            await geocode("ZZZnonexistent")


async def test_geocode_missing_results_key():
    mock_response = MagicMock()
    mock_response.json.return_value = {}  # no "results" key at all
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.weather.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Location not found"):
            await geocode("UnknownPlace")


# ---------------------------------------------------------------------------
# Location resolution
# ---------------------------------------------------------------------------


async def test_resolve_location_latlon():
    """Providing lat+lon skips geocoding entirely."""
    with patch("app.weather.geocode", new_callable=AsyncMock) as mock_geocode:
        lat, lon = await resolve_location(None, 48.8566, 2.3522)

    mock_geocode.assert_not_called()
    assert lat == pytest.approx(48.8566)
    assert lon == pytest.approx(2.3522)


async def test_resolve_location_city():
    with patch(
        "app.weather.geocode", new_callable=AsyncMock, return_value=(35.6895, 139.6917)
    ) as mock_geocode:
        lat, lon = await resolve_location("Tokyo", None, None)

    mock_geocode.assert_awaited_once_with("Tokyo")
    assert lat == pytest.approx(35.6895)
    assert lon == pytest.approx(139.6917)


async def test_resolve_location_no_input():
    with pytest.raises(ValueError, match="Provide either"):
        await resolve_location(None, None, None)


# ---------------------------------------------------------------------------
# Open-Meteo provider
# ---------------------------------------------------------------------------


def _make_client_mock(json_data: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client


async def test_openmeteo_current():
    payload = {
        "current": {
            "temperature_2m": 15.3,
            "apparent_temperature": 13.1,
            "relative_humidity_2m": 72,
            "wind_speed_10m": 18.5,
            "weather_code": 2,
        }
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        result = await OpenMeteoProvider().get_current(51.5, -0.1)

    assert result.temp_celsius == 15.3
    assert result.feels_like_celsius == 13.1
    assert result.humidity_percent == 72
    assert result.wind_speed_kmh == 18.5
    assert result.weather_code == 2
    assert result.description == "Partly cloudy"


async def test_openmeteo_current_unknown_code():
    payload = {
        "current": {
            "temperature_2m": 10.0,
            "apparent_temperature": 9.0,
            "relative_humidity_2m": 50,
            "wind_speed_10m": 5.0,
            "weather_code": 999,
        }
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        result = await OpenMeteoProvider().get_current(0.0, 0.0)

    assert result.description == "WMO code 999"


async def test_openmeteo_forecast():
    payload = {
        "daily": {
            "time": ["2026-03-26", "2026-03-27"],
            "temperature_2m_max": [18.0, 20.5],
            "temperature_2m_min": [10.0, 12.0],
            "precipitation_sum": [0.0, 2.3],
            "weather_code": [0, 63],
        }
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        result = await OpenMeteoProvider().get_forecast(51.5, -0.1, 2)

    assert len(result.days) == 2
    day0 = result.days[0]
    assert day0.date == "2026-03-26"
    assert day0.temp_max_celsius == 18.0
    assert day0.temp_min_celsius == 10.0
    assert day0.precipitation_mm == 0.0
    assert day0.description == "Clear sky"
    assert result.days[1].description == "Moderate rain"


async def test_openmeteo_forecast_days_capped():
    """Days param should be clamped to [1, 16]."""
    payload = {
        "daily": {
            "time": [],
            "temperature_2m_max": [],
            "temperature_2m_min": [],
            "precipitation_sum": [],
            "weather_code": [],
        }
    }
    mock_client = _make_client_mock(payload)
    with patch("app.weather.httpx.AsyncClient", return_value=mock_client):
        await OpenMeteoProvider().get_forecast(0.0, 0.0, 999)

    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["params"]["forecast_days"] == 16


# ---------------------------------------------------------------------------
# OpenWeatherMap provider
# ---------------------------------------------------------------------------


async def test_openweathermap_current():
    payload = {
        "main": {"temp": 22.0, "feels_like": 20.5, "humidity": 65},
        "wind": {"speed": 5.0},  # m/s → 18.0 km/h
        "weather": [{"id": 800, "description": "clear sky"}],
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        result = await OpenWeatherMapProvider("testkey").get_current(48.8, 2.3)

    assert result.temp_celsius == 22.0
    assert result.feels_like_celsius == 20.5
    assert result.humidity_percent == 65
    assert result.wind_speed_kmh == pytest.approx(18.0)
    assert result.weather_code == 800
    assert result.description == "Clear sky"


async def test_openweathermap_forecast_aggregation():
    """Three-hour slots should be aggregated into daily buckets."""
    payload = {
        "list": [
            {
                "dt_txt": "2026-03-26 00:00:00",
                "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 80},
                "weather": [{"id": 500, "description": "light rain"}],
                "rain": {"3h": 1.5},
            },
            {
                "dt_txt": "2026-03-26 03:00:00",
                "main": {"temp": 12.0, "feels_like": 11.0, "humidity": 75},
                "weather": [{"id": 500, "description": "light rain"}],
                "rain": {"3h": 0.5},
            },
            {
                "dt_txt": "2026-03-27 00:00:00",
                "main": {"temp": 18.0, "feels_like": 17.0, "humidity": 60},
                "weather": [{"id": 800, "description": "clear sky"}],
            },
        ]
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        result = await OpenWeatherMapProvider("testkey").get_forecast(48.8, 2.3, 2)

    assert len(result.days) == 2
    day0 = result.days[0]
    assert day0.date == "2026-03-26"
    assert day0.temp_max_celsius == 12.0
    assert day0.temp_min_celsius == 10.0
    assert day0.precipitation_mm == pytest.approx(2.0)
    day1 = result.days[1]
    assert day1.date == "2026-03-27"
    assert day1.description == "Clear sky"


async def test_openweathermap_forecast_days_capped():
    payload = {"list": []}
    mock_client = _make_client_mock(payload)
    with patch("app.weather.httpx.AsyncClient", return_value=mock_client):
        await OpenWeatherMapProvider("key").get_forecast(0.0, 0.0, 99)

    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["params"]["cnt"] == 5 * 8


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------


def test_get_provider_default(monkeypatch):
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    provider = get_provider()
    assert isinstance(provider, OpenMeteoProvider)


def test_get_provider_owm(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "mykey123")
    provider = get_provider()
    assert isinstance(provider, OpenWeatherMapProvider)
    assert provider._api_key == "mykey123"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


async def test_openmeteo_current_validation_error():
    """Missing required field in API response raises ValidationError."""
    payload = {
        "current": {
            # temperature_2m is missing
            "apparent_temperature": 13.1,
            "relative_humidity_2m": 72,
            "wind_speed_10m": 18.5,
            "weather_code": 2,
        }
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        with pytest.raises(ValidationError):
            await OpenMeteoProvider().get_current(51.5, -0.1)


async def test_openweathermap_current_validation_error():
    """Missing required field in OWM API response raises ValidationError."""
    payload = {
        "main": {"temp": 22.0, "feels_like": 20.5, "humidity": 65},
        # "wind" key is missing
        "weather": [{"id": 800, "description": "clear sky"}],
    }
    with patch(
        "app.weather.httpx.AsyncClient", return_value=_make_client_mock(payload)
    ):
        with pytest.raises(ValidationError):
            await OpenWeatherMapProvider("testkey").get_current(48.8, 2.3)
