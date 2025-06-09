from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import Context


@pytest.fixture
def mock_context():
    """Create a mock MCP Context for testing."""
    ctx = AsyncMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture
def sample_weather_response():
    """Sample successful weather API response."""
    return {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "temp_min": 12.0,
            "temp_max": 18.0,
            "pressure": 1013,
            "humidity": 65,
        },
        "wind": {"speed": 3.5, "deg": 220},
        "clouds": {"all": 0},
        "dt": 1609459200,
        "sys": {"country": "GB", "sunrise": 1609398000, "sunset": 1609427000},
        "timezone": 0,
        "id": 2643743,
        "name": "London",
    }


@pytest.fixture
def sample_geocoding_response():
    """Sample successful geocoding API response."""
    return [
        {
            "name": "New York",
            "lat": 40.7127281,
            "lon": -74.0060152,
            "country": "US",
            "state": "New York",
            "local_names": {"en": "New York", "es": "Nueva York", "fr": "New York"},
        }
    ]


@pytest.fixture
def sample_reverse_geocoding_response():
    """Sample successful reverse geocoding API response."""
    return [
        {
            "name": "New York",
            "lat": 40.7128,
            "lon": -74.0060,
            "country": "US",
            "state": "New York",
            "local_names": {"en": "New York", "es": "Nueva York"},
        }
    ]


@pytest.fixture
def sample_forecast_response():
    """Sample Weather Forecast response."""
    return {
        "cod": "200",
        "message": 0,
        "cnt": 40,
        "list": [
            {
                "dt": 1640995200,  # 2022-01-01 00:00:00 UTC
                "main": {
                    "temp": 15.5,
                    "feels_like": 14.2,
                    "temp_min": 14.8,
                    "temp_max": 16.1,
                    "pressure": 1013,
                    "sea_level": 1013,
                    "grnd_level": 1011,
                    "humidity": 65,
                    "temp_kf": -0.3,
                },
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d",
                    }
                ],
                "clouds": {"all": 5},
                "wind": {"speed": 3.2, "deg": 180, "gust": 4.1},
                "visibility": 10000,
                "pop": 0.1,
                "sys": {"pod": "d"},
                "dt_txt": "2022-01-01 00:00:00",
            },
            {
                "dt": 1641006000,  # 2022-01-01 03:00:00 UTC
                "main": {
                    "temp": 18.2,
                    "feels_like": 17.1,
                    "temp_min": 17.5,
                    "temp_max": 18.8,
                    "pressure": 1012,
                    "humidity": 58,
                    "temp_kf": -0.2,
                },
                "weather": [
                    {
                        "id": 801,
                        "main": "Clouds",
                        "description": "few clouds",
                        "icon": "02d",
                    }
                ],
                "clouds": {"all": 20},
                "wind": {"speed": 2.8, "deg": 200},
                "visibility": 10000,
                "pop": 0.05,
                "rain": {"3h": 0.2},
                "sys": {"pod": "d"},
                "dt_txt": "2022-01-01 03:00:00",
            },
        ],
        "city": {
            "id": 2643743,
            "name": "London",
            "coord": {"lat": 51.5085, "lon": -0.1257},
            "country": "GB",
            "population": 1000000,
            "timezone": 0,
            "sunrise": 1640935200,
            "sunset": 1640965200,
        },
    }


@pytest.fixture
def sample_air_pollution_response():
    """Sample air pollution API response."""
    return {
        "coord": {"lon": -74.006, "lat": 40.7128},
        "list": [
            {
                "dt": int(datetime.now().timestamp()),
                "main": {"aqi": 3},
                "components": {
                    "co": 233.4,
                    "no": 0.01,
                    "no2": 18.4,
                    "o3": 168.8,
                    "so2": 0.64,
                    "pm2_5": 9.3,
                    "pm10": 16.7,
                    "nh3": 0.72,
                },
            }
        ],
    }


@pytest.fixture
def sample_air_pollution_forecast_response():
    """Sample air pollution forecast API response."""
    now = datetime.now()
    return {
        "coord": {"lon": -74.006, "lat": 40.7128},
        "list": [
            {
                "dt": int((now + timedelta(hours=i)).timestamp()),
                "main": {"aqi": 2 + (i % 3)},
                "components": {
                    "co": 200.0 + i * 10,
                    "no": 0.01,
                    "no2": 15.0 + i * 2,
                    "o3": 150.0 + i * 5,
                    "so2": 0.5,
                    "pm2_5": 8.0 + i * 1.5,
                    "pm10": 15.0 + i * 2,
                    "nh3": 0.7,
                },
            }
            for i in range(120)  # 5 days * 24 hours
        ],
    }


@pytest.fixture
def sample_air_pollution_historical_response():
    start_time = int((datetime.now() - timedelta(days=30)).timestamp())
    return {
        "coord": {"lon": -74.006, "lat": 40.7128},
        "list": [
            {
                "dt": start_time + i * 3600,
                "main": {"aqi": 2},
                "components": {"pm2_5": 10.0, "pm10": 18.0, "no2": 20.0},
            }
            for i in range(100)
        ],
    }


@pytest.fixture
def sample_geo_response():
    """Sample geocoding API response."""
    return [
        {
            "name": "New York",
            "lat": 40.7128,
            "lon": -74.006,
            "country": "US",
            "state": "NY",
        }
    ]
