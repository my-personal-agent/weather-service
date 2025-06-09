import logging
from typing import Any

from mcp.server.fastmcp import Context

from core.annotated import (
    ANNOTATED_CITY,
    ANNOTATED_LANG,
    ANNOTATED_LAT,
    ANNOTATED_LON,
    ANNOTATED_OPTIONAL_COUNTRY_CODE,
)
from enums.openweather import OpenWeatherEndpoint
from weather_mcp.server import mcp
from weather_mcp.utils import call_openweather_api

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_current_weather_by_geo(
    ctx: Context,
    lat: ANNOTATED_LAT,
    lon: ANNOTATED_LON,
    lang: ANNOTATED_LANG = "en",
) -> dict[str, Any]:
    """
    Get current weather conditions for a specific geographic location using latitude and longitude coordinates.

    **Function Description:**
    Retrieves real-time weather data from OpenWeatherMap API using precise geographic coordinates.
    Returns comprehensive weather information including temperature, humidity, wind speed, and atmospheric conditions.

    **Args:**
        lat (float): Latitude coordinate (-90.0 to 90.0). Positive values for North, negative for South.
                    Higher precision (4+ decimal places) provides more accurate location matching.
        lon (float): Longitude coordinate (-180.0 to 180.0). Positive values for East, negative for West.
                    Higher precision (4+ decimal places) provides more accurate location matching.
        lang (str, optional): Language code for weather descriptions. Defaults to "en" (English).
                              Supports 40+ languages: en, es, fr, de, it, pt, ru, ja, zh_cn, zh_tw,
                              ar, bg, ca, cz, da, el, fa, fi, gl, he, hi, hr, hu, kr, la, lt, lv,
                              mk, nl, no, pl, ro, sk, sl, sv, th, tr, ua, vi, zu

    **Returns:**
        dict: Weather data containing:
            - coord: {lat, lon} - Geographic coordinates
            - weather: List of weather conditions with id, main, description, icon
            - main: Temperature data (temp, feels_like, temp_min, temp_max, pressure, humidity)
            - wind: Wind information (speed, deg, gust)
            - clouds: Cloud coverage percentage
            - dt: Data calculation timestamp
            - sys: System data (country, sunrise, sunset)
            - timezone: Timezone offset from UTC
            - name: Location name

    **Raises:**
        ValueError: If coordinates are out of valid range (-90≤lat≤90, -180≤lon≤180)
        ToolError: If OpenWeatherMap API returns error status
        ToolError: If network request fails or times out

    **Usage Examples:**
        # Get weather for Tokyo, Japan
        weather = await get_current_weather_by_geo(35.6762, 139.6503)

        # Get weather for New York with Spanish descriptions
        weather = await get_current_weather_by_geo(40.7128, -74.0060, lang="es")

        # Extract temperature and conditions
        temp = weather['main']['temp']
        description = weather['weather'][0]['description']
        print(f"Temperature: {temp}°C, Conditions: {description}")

    **MCP Integration Notes:**
        - This tool is automatically exposed to MCP clients when server starts
        - Coordinate validation happens before API call to prevent unnecessary requests
        - Returns structured data that MCP clients can easily parse and display
        - Consider rate limiting in high-frequency scenarios (OpenWeather has usage limits)
        - Tool will appear in MCP client's available functions list

    **Data Processing Tips:**
        - Temperature is in Celsius by default (add units=imperial for Fahrenheit)
        - Wind speed is in meters/second (multiply by 2.237 for mph)
        - Pressure is in hPa (hectopascals)
        - Visibility is in meters (divide by 1000 for kilometers)
        - Timestamps are Unix UTC - convert using datetime.fromtimestamp()
        - Weather icons can be displayed using: http://openweathermap.org/img/w/{icon}.png

    **Common Use Cases:**
        - Location-based mobile apps showing local weather
        - IoT devices reporting environmental conditions
        - Travel planning applications
        - Agricultural monitoring systems
        - Event planning platforms checking weather conditions
        - Logistics apps for weather-dependent operations
    """
    params = {"lat": lat, "lon": lon, "lang": lang}
    return await call_openweather_api(
        OpenWeatherEndpoint.CURRENT_WEATHER, params, mcp_ctx=ctx
    )


@mcp.tool()
async def get_current_weather_by_city(
    ctx: Context,
    city: ANNOTATED_CITY,
    country_code: ANNOTATED_OPTIONAL_COUNTRY_CODE = None,
    lang: ANNOTATED_LANG = "en",
) -> dict[str, Any]:
    """
    Get current weather conditions for a city by name, with optional country specification.

    **Function Description:**
    Retrieves real-time weather data from OpenWeatherMap API using city name search.
    More user-friendly than coordinates but may be less precise for cities with duplicate names.
    Automatically handles city name resolution and geocoding.

    **Args:**
        city (str): City name (e.g., "London", "New York", "São Paulo", "東京").
                   Case-insensitive, supports Unicode characters and diacritics.
                   Can include state/province for US/CA cities (e.g., "Austin,TX").
        country_code (Optional[str], optional): ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP").
                                               Strongly recommended for cities with duplicate names.
                                               Helps ensure forecast accuracy for intended location.
                                               Defaults to None (global search, returns best match).
        lang (str, optional): Language code for weather descriptions. Defaults to "en" (English).
                              Supports 40+ languages: en, es, fr, de, it, pt, ru, ja, zh_cn, zh_tw,
                              ar, bg, ca, cz, da, el, fa, fi, gl, he, hi, hr, hu, kr, la, lt, lv,
                              mk, nl, no, pl, ro, sk, sl, sv, th, tr, ua, vi, zu

    **Returns:**
        dict: Same structure as get_current_weather_by_geo():
            - coord: {lat, lon} - Resolved geographic coordinates
            - weather: Weather conditions array
            - main: Temperature and atmospheric data
            - wind: Wind measurements
            - clouds: Cloud coverage
            - dt: Data timestamp
            - sys: System info including country code
            - timezone: UTC offset in seconds
            - name: Resolved city name
            - id: City ID for future reference

    **Raises:**
        ValueError: If city name is empty, too short, or contains invalid characters
        ValueError: If country_code format is invalid (not 2-letter ISO code)
        ToolError: If city name cannot be resolved, doesn't exist, or is ambiguous
        ToolError: If OpenWeatherMap API returns error status
        ToolError: If network request fails or times out

    **Usage Examples:**
        # Basic city lookup
        weather = await get_current_weather_by_city("Paris")

        # Specify country to avoid ambiguity
        weather = await get_current_weather_by_city("Paris", country_code="FR")

        # Get weather in local language
        weather = await get_current_weather_by_city("Moscow", country_code="RU", lang="ru")

        # Handle multiple cities with same name
        london_uk = await get_current_weather_by_city("London", "GB")
        london_ca = await get_current_weather_by_city("London", "CA")

        # Extract key information
        location = f"{weather['name']}, {weather['sys']['country']}"
        temp = weather['main']['temp']
        humidity = weather['main']['humidity']

    **MCP Integration Notes:**
        - Ideal for conversational interfaces where users provide city names
        - MCP clients can offer city name autocompletion using this function
        - Consider caching results for frequently requested cities
        - Function handles internationalization automatically
        - Error messages are user-friendly for MCP client display

    **Data Processing Tips:**
        - City names are normalized by the API (case/accent insensitive)
        - Country codes should be ISO 3166-1 alpha-2 format (2 letters)
        - API returns the "best match" city if multiple exist
        - Store the returned city ID for faster future lookups
        - Weather descriptions respect the lang parameter for localization
        - Coordinate data is included for mapping/visualization needs

    **Common Use Cases:**
        - Chat bots answering "What's the weather in [city]?" queries
        - Travel websites showing destination weather
        - News applications displaying weather for story locations
        - Social media apps showing weather for user's posted location
        - Voice assistants handling weather inquiries
        - International business apps showing weather at office locations
        - Event management platforms for venue weather checking
    """
    location = f"{city},{country_code}" if country_code else city
    params = {"q": location, "lang": lang}

    return await call_openweather_api(
        OpenWeatherEndpoint.CURRENT_WEATHER, params, mcp_ctx=ctx
    )
