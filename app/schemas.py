"""Pydantic models for HTTP API response validation and normalized output."""

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Open-Meteo geocoding response
# ---------------------------------------------------------------------------


class _GeoResult(BaseModel):
    latitude: float
    longitude: float


class _GeoResponse(BaseModel):
    results: list[_GeoResult] | None = None


# ---------------------------------------------------------------------------
# Open-Meteo current weather response
# ---------------------------------------------------------------------------


class _OMCurrentFields(BaseModel):
    temperature_2m: float
    apparent_temperature: float
    relative_humidity_2m: int
    wind_speed_10m: float
    weather_code: int


class _OMCurrentResponse(BaseModel):
    current: _OMCurrentFields


# ---------------------------------------------------------------------------
# Open-Meteo forecast response
# ---------------------------------------------------------------------------


class _OMDailyFields(BaseModel):
    time: list[str]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    precipitation_sum: list[float]
    weather_code: list[int]


class _OMForecastResponse(BaseModel):
    daily: _OMDailyFields


# ---------------------------------------------------------------------------
# OpenWeatherMap current weather response
# ---------------------------------------------------------------------------


class _OWMMain(BaseModel):
    temp: float
    feels_like: float
    humidity: int


class _OWMWind(BaseModel):
    speed: float


class _OWMWeatherItem(BaseModel):
    id: int
    description: str


class _OWMCurrentResponse(BaseModel):
    main: _OWMMain
    wind: _OWMWind
    weather: list[_OWMWeatherItem]


# ---------------------------------------------------------------------------
# OpenWeatherMap forecast response (3-hour slots)
# ---------------------------------------------------------------------------


class _OWMPrecip(BaseModel):
    h3: float = Field(default=0.0, validation_alias="3h")


class _OWMForecastEntry(BaseModel):
    dt_txt: str
    main: _OWMMain
    weather: list[_OWMWeatherItem]
    rain: _OWMPrecip | None = None
    snow: _OWMPrecip | None = None


class _OWMForecastResponse(BaseModel):
    list: list[_OWMForecastEntry]


# ---------------------------------------------------------------------------
# Normalized output models (returned by providers)
# ---------------------------------------------------------------------------


class CurrentWeather(BaseModel):
    temp_celsius: float
    feels_like_celsius: float
    humidity_percent: int
    wind_speed_kmh: float
    weather_code: int
    description: str


class ForecastDay(BaseModel):
    date: str
    temp_max_celsius: float
    temp_min_celsius: float
    precipitation_mm: float
    weather_code: int
    description: str


class Forecast(BaseModel):
    days: list[ForecastDay]
