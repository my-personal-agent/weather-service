from enum import Enum


class OpenWeatherEndpoint(str, Enum):
    CURRENT_WEATHER = "weather"
    FORECAST = "forecast"
    FORECAST_HOURLY = "forecast/hourly"
    FORECAST_DAILY = "forecast/daily"
    CURRENT_AIR_POLLUTION = "air_pollution"
    FORECAST_AIR_POLLUTION = "air_pollution/forecast"
    HISTORICAL_AIR_POLLUTION = "air_pollution/history"
    DIRECT_GEOCODING = "direct"
    REVERSE_GEOCODING = "reverse"
