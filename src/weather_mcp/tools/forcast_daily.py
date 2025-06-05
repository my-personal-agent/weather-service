import logging

from mcp.server.fastmcp.exceptions import ToolError

from enums.openweather import OpenWeatherEndpoint
from core.http_client import call_openweather_api
from weather_mcp.utils import check_geo, handle_error

logger = logging.getLogger(__name__)


def check_cnt(cnt: int | None) -> None:
    """
    Validates the 'cnt' parameter for the number of forecast days.

    Args:
        cnt (int | None): The number of forecast days requested.

    Raises:
        ToolError: If cnt is not between 1 and 16.
    """
    if cnt is not None and not (1 <= cnt <= 16):
        raise ToolError("The number of forecast days (cnt) must be between 1 and 16.")


# @mcp.tool()
async def get_forecast_daily_by_geo(
    lat: float, lon: float, cnt: int | None = None, lang: str = "en"
) -> dict:
    """
    Get daily weather forecast for a specific geographic location using latitude and longitude coordinates.

    **Function Description:**
    Retrieves extended daily weather forecasts from OpenWeatherMap API using precise geographic coordinates.
    Provides up to 16 days of forecast data with daily granularity, including temperature ranges,
    precipitation totals, wind patterns, and atmospheric conditions. Perfect for medium to long-term
    weather planning, seasonal analysis, and applications requiring precise location-based extended forecasting.
    Each day includes morning, day, evening, and night temperature breakdowns.

    **Args:**
        lat (float): Latitude coordinate (-90.0 to 90.0). Positive values for North, negative for South.
                    Higher precision (4+ decimal places) provides more accurate location matching.
        lon (float): Longitude coordinate (-180.0 to 180.0). Positive values for East, negative for West.
                    Higher precision (4+ decimal places) provides more accurate location matching.
        cnt (int | None, optional): Number of days to forecast (1-16). Defaults to None (returns maximum 16 days).
                                   Useful for limiting response size and API usage for shorter-term needs.
                                   Values outside 1-16 range will be validated and may raise errors.
        lang (str, optional): Language code for weather descriptions. Defaults to "en" (English).
                              Supports 40+ languages: en, es, fr, de, it, pt, ru, ja, zh_cn, zh_tw,
                              ar, bg, ca, cz, da, el, fa, fi, gl, he, hi, hr, hu, kr, la, lt, lv,
                              mk, nl, no, pl, ro, sk, sl, sv, th, tr, ua, vi, zu

    **Returns:**
        dict: Daily forecast data containing:
            - cod: Response code (200 for success)
            - message: Response message and metadata
            - city: Location information (id, name, coord, country, population, timezone)
            - cnt: Actual number of forecast days returned
            - list: Array of daily forecast objects (1-16 entries), each containing:
                * dt: Forecast date timestamp (Unix UTC, noon time)
                * sunrise: Sunrise timestamp (Unix UTC)
                * sunset: Sunset timestamp (Unix UTC)
                * moonrise: Moonrise timestamp (Unix UTC)
                * moonset: Moonset timestamp (Unix UTC)
                * moon_phase: Moon phase (0-1, where 0/1=new moon, 0.5=full moon)
                * summary: Brief weather summary text
                * temp: Temperature object (morn, day, eve, night, min, max)
                * feels_like: Perceived temperature object (morn, day, eve, night)
                * pressure: Atmospheric pressure (hPa)
                * humidity: Humidity percentage (0-100)
                * weather: Weather conditions array (id, main, description, icon)
                * speed: Wind speed (m/s)
                * deg: Wind direction (degrees, 0-360)
                * gust: Wind gust speed (m/s, if applicable)
                * clouds: Cloud coverage percentage (0-100)
                * pop: Probability of precipitation (0.0-1.0)
                * rain: Rain volume (mm, if applicable)
                * snow: Snow volume (mm, if applicable)
                * uvi: UV Index maximum for the day

    **Raises:**
        ValueError: If coordinates are out of valid range (-90≤lat≤90, -180≤lon≤180)
        CountError: If cnt parameter is outside valid range (1-16) or invalid type
        APIError: If OpenWeatherMap API returns error status (401, 404, 429, 5xx)
        NetworkError: If network request fails, times out, or connection is unstable

    **Usage Examples:**
        # Get full 16-day forecast for London coordinates
        forecast = await get_forecast_daily_by_geo(51.5074, -0.1278)

        # Get 7-day forecast for Tokyo with Japanese descriptions
        forecast = await get_forecast_daily_by_geo(35.6762, 139.6503, cnt=7, lang="ja")

        # Get 3-day forecast for specific outdoor event location
        event_forecast = await get_forecast_daily_by_geo(34.0522, -118.2437, cnt=3)

        # Process daily temperature ranges
        for day in forecast['list']:
            date = datetime.fromtimestamp(day['dt']).strftime('%Y-%m-%d')
            temp_min = day['temp']['min']
            temp_max = day['temp']['max']
            conditions = day['weather'][0]['description']
            rain_chance = day['pop'] * 100
            print(f"{date}: {temp_min}°-{temp_max}°C, {conditions}, {rain_chance}% rain")

        # Find best days for outdoor activities (good weather window)
        good_days = []
        for day in forecast['list']:
            if (day['temp']['max'] > 20 and day['temp']['min'] > 10 and
                day['pop'] < 0.3 and day['clouds'] < 50):
                date = datetime.fromtimestamp(day['dt'])
                good_days.append(date)

        # Calculate weekly temperature trends
        temps = [day['temp']['day'] for day in forecast['list'][:7]]
        avg_temp = sum(temps) / len(temps)
        temp_trend = "warming" if temps[-1] > temps[0] else "cooling"

        # Check for extreme weather alerts
        extreme_days = []
        for day in forecast['list']:
            if (day['temp']['max'] > 35 or day['temp']['min'] < 0 or
                day['speed'] > 10 or day.get('rain', 0) > 20):
                extreme_days.append({
                    'date': datetime.fromtimestamp(day['dt']),
                    'conditions': day['weather'][0]['description'],
                    'temp_range': f"{day['temp']['min']}-{day['temp']['max']}°C"
                })

    **MCP Integration Notes:**
        - Ideal for MCP clients requiring extended weather planning capabilities
        - Moderate response size (16 days max) - suitable for most MCP message limits
        - Consider implementing date range selectors in MCP client UI (1, 3, 7, 14 day options)
        - Cache responses for 6-12 hours as daily forecasts change less frequently
        - MCP clients can create weather calendars and trend visualizations from daily data
        - Expose summary statistics (average temps, total precipitation) for quick client display
        - Consider chunking display by weeks for better user experience
        - Enable client-side filtering by weather conditions or temperature ranges

    **Data Processing Tips:**
        - All timestamps are Unix UTC - convert using datetime.fromtimestamp() with timezone awareness
        - Apply city.timezone offset for accurate local date display
        - Temperature breakdown: morn (6-12), day (12-18), eve (18-24), night (0-6 local time)
        - Daily timestamp (dt) represents noon UTC for the forecast day
        - Moon phase: 0=new moon, 0.25=first quarter, 0.5=full moon, 0.75=last quarter
        - UV Index ranges: 0-2 (low), 3-5 (moderate), 6-7 (high), 8-10 (very high), 11+ (extreme)
        - Precipitation probability (pop) is maximum chance during the day
        - Wind direction: 0°=North, 90°=East, 180°=South, 270°=West
        - Aggregate rain/snow volumes represent total daily accumulation
        - Use summary field for human-readable weather overview

    **Common Use Cases:**
        - Event planning and venue management for outdoor activities and weddings
        - Agricultural planning for planting, harvesting, and crop protection schedules
        - Travel and tourism applications showing destination weather for trip duration
        - Construction and infrastructure projects requiring weather-sensitive scheduling
        - Energy sector planning for solar/wind generation and demand forecasting
        - Retail and hospitality for inventory planning and staffing based on weather patterns
        - Sports and recreation apps helping users plan outdoor activities
        - Emergency preparedness systems for weather-related risk assessment
        - Insurance applications for weather-related claim risk analysis
        - Transportation and logistics for long-term route and schedule planning
        - Real estate applications showing seasonal weather patterns for property locations
    """
    check_geo(lat, lon)
    check_cnt(cnt)

    params = {"lat": lat, "lon": lon, "lang": lang}
    if cnt is not None:
        params["cnt"] = str(cnt)

    try:
        return await call_openweather_api(OpenWeatherEndpoint.FORECAST_DAILY, params)

    except Exception as e:
        raise handle_error(e)


# @mcp.tool()
async def get_forecast_daily_by_city(
    city: str, country_code: str | None = None, cnt: int | None = None, lang: str = "en"
) -> dict:
    """
    Get daily weather forecast for a city by name, with optional country specification and day count control.

    **Function Description:**
    Retrieves extended daily weather forecasts from OpenWeatherMap API using city name search with flexible
    duration control. Provides up to 16 days of detailed daily weather data for user-friendly city-based queries.
    More accessible than coordinate-based lookup while maintaining full forecast detail and customizable time ranges.
    Automatically handles city name resolution, geocoding, timezone determination, and ambiguity resolution
    when combined with country codes.

    **Args:**
        city (str): City name (e.g., "London", "New York", "São Paulo", "東京").
                   Case-insensitive, supports Unicode characters and diacritics.
                   Can include state/province for US/CA cities (e.g., "Austin,TX").
        country_code (str | None, optional): ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP").
                                           Strongly recommended for cities with duplicate names.
                                           Helps ensure forecast accuracy for intended location.
                                           Defaults to None (global search, returns best match).
        cnt (int | None, optional): Number of forecast days to return (1-16). Defaults to None (maximum 16 days).
                                   Useful for controlling response size, API usage, and client display complexity.
                                   Common values: 1 (tomorrow), 3 (weekend), 7 (week), 14 (two weeks).
        lang (str, optional): Language code for weather descriptions. Defaults to "en" (English).
                              Supports 40+ languages: en, es, fr, de, it, pt, ru, ja, zh_cn, zh_tw,
                              ar, bg, ca, cz, da, el, fa, fi, gl, he, hi, hr, hu, kr, la, lt, lv,
                              mk, nl, no, pl, ro, sk, sl, sv, th, tr, ua, vi, zu

    **Returns:**
        dict: Complete daily forecast structure identical to get_forecast_daily_by_geo():
            - cod: HTTP response code (200 for success)
            - message: API response metadata
            - cnt: Actual number of days returned (may be less than requested if API limits)
            - city: Comprehensive city information including:
                * id: OpenWeatherMap city identifier (cache this for faster future requests)
                * name: Resolved city name (may be normalized from input)
                * coord: {lat, lon} - Precise coordinates for mapping and other location services
                * country: ISO country code (verified location)
                * population: Estimated city population
                * timezone: UTC offset in seconds for local time calculations
            - list: Array of daily forecast objects with complete weather data per day

    **Raises:**
        CityNotFoundError: If city name cannot be resolved, doesn't exist in API database
        CountryCodeError: If country_code format is invalid (not 2-letter ISO format)
        CountError: If cnt parameter is outside valid range (1-16) or wrong data type
        APIError: If OpenWeatherMap API returns error status
        NetworkError: If network request fails or times out
        ValidationError: If city name is empty, too short, or contains invalid characters
        AmbiguousLocationError: If multiple cities match and no country_code provided

    **Usage Examples:**
        # Basic 16-day city forecast
        forecast = await get_forecast_daily_by_city("Paris")

        # 7-day forecast with country disambiguation
        london_uk = await get_forecast_daily_by_city("London", "GB", cnt=7)
        london_on = await get_forecast_daily_by_city("London", "CA", cnt=7)

        # 3-day weekend forecast with local language
        weekend = await get_forecast_daily_by_city("Barcelona", "ES", cnt=3, lang="es")

        # Business planning: check weather for next work week
        work_week = await get_forecast_daily_by_city("Chicago", "US", cnt=5)
        business_impact = []
        for day in work_week['list']:
            date = datetime.fromtimestamp(day['dt'])
            if date.weekday() < 5:  # Monday-Friday
                impact_score = 0
                if day['pop'] > 0.7: impact_score += 2  # High rain probability
                if day['temp']['max'] > 35 or day['temp']['min'] < 0: impact_score += 3  # Extreme temps
                if day['speed'] > 8: impact_score += 1  # High wind
                business_impact.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'impact': 'high' if impact_score > 3 else 'medium' if impact_score > 1 else 'low',
                    'conditions': day['weather'][0]['description']
                })

        # Travel planning: find best weather window
        trip_forecast = await get_forecast_daily_by_city("Rome", "IT", cnt=10)
        best_days = []
        for i, day in enumerate(trip_forecast['list']):
            score = 0
            # Scoring: good temperature range, low precipitation, moderate clouds
            if 18 <= day['temp']['day'] <= 26: score += 3
            if day['pop'] < 0.2: score += 2
            if day['clouds'] < 30: score += 1
            if day['uvi'] < 8: score += 1  # Not too intense UV

            if score >= 5:  # Excellent weather day
                best_days.append({
                    'date': datetime.fromtimestamp(day['dt']).strftime('%A, %B %d'),
                    'temp': f"{day['temp']['min']:.1f}-{day['temp']['max']:.1f}°C",
                    'conditions': day['weather'][0]['description'],
                    'score': score
                })

        # Agricultural planning: frost and precipitation analysis
        farm_forecast = await get_forecast_daily_by_city("Des Moines", "US", cnt=14)
        frost_risk_days = []
        heavy_rain_days = []

        for day in farm_forecast['list']:
            date = datetime.fromtimestamp(day['dt'])
            if day['temp']['min'] <= 2:  # Frost risk
                frost_risk_days.append(date)
            if day.get('rain', 0) > 15:  # Heavy rain
                heavy_rain_days.append(date)

        # Event planning: outdoor wedding weather assessment
        wedding_date = await get_forecast_daily_by_city("Napa", "US", cnt=1)
        wedding_day = wedding_date['list'][0]
        suitability = {
            'temperature': 'ideal' if 20 <= wedding_day['temp']['day'] <= 28 else 'acceptable',
            'precipitation': 'concerning' if wedding_day['pop'] > 0.3 else 'good',
            'wind': 'problematic' if wedding_day['speed'] > 7 else 'acceptable',
            'overall_rating': wedding_day['weather'][0]['main'],
            'backup_plan_needed': wedding_day['pop'] > 0.4 or wedding_day['speed'] > 8
        }

    **MCP Integration Notes:**
        - Perfect for conversational MCP interfaces handling natural language weather queries
        - Implement smart city name suggestions and autocomplete in MCP clients
        - Store city.id from responses for 15% faster subsequent API calls
        - MCP clients should provide intuitive day count selection (tomorrow, weekend, week, two weeks)
        - Handle city disambiguation gracefully by presenting options to users
        - Consider implementing weather alerts and notifications for extreme conditions
        - Cache city-based forecasts for 4-8 hours to optimize performance
        - Provide weather summary cards and detailed drill-down views in MCP UI
        - Enable location-aware suggestions based on user's current or frequently searched cities

    **Data Processing Tips:**
        - Always verify resolved city name and country match user expectations
        - Use city.timezone for accurate local time and date display
        - Store and reuse city.id for performance optimization (cache city lookups)
        - Daily forecasts represent calendar days in local timezone, not 24-hour periods from request time
        - Temperature fields (morn/day/eve/night) correspond to local time periods
        - Combine current weather with daily forecast for comprehensive location intelligence
        - Moon phase data useful for outdoor activity planning and photography
        - UV index critical for health applications and outdoor event planning
        - Consider weather pattern analysis across multiple days for trend identification
        - Precipitation totals are cumulative for entire calendar day

    **Common Use Cases:**
        - Travel and vacation planning with destination weather analysis
        - Voice assistants providing extended weather outlooks for cities
        - Business applications monitoring weather across multiple office locations
        - Social media platforms showing weather context for location-tagged posts
        - Event management systems for outdoor venue and date selection
        - News and media applications providing weather stories for specific cities
        - Agricultural and farming applications for multi-location crop monitoring
        - International logistics and shipping for weather-sensitive cargo planning
        - Tourism and hospitality websites helping visitors plan extended stays
        - Educational applications teaching weather patterns and climate analysis
        - Emergency management systems for multi-day weather preparedness planning
    """
    check_cnt(cnt)

    location = f"{city},{country_code}" if country_code else city
    params = {"q": location, "lang": lang}
    if cnt is not None:
        params["cnt"] = str(cnt)

    try:
        return await call_openweather_api(OpenWeatherEndpoint.FORECAST_DAILY, params)

    except Exception as e:
        raise handle_error(e)
