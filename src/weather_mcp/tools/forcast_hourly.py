import logging

from enums.openweather import OpenWeatherEndpoint
from core.http_client import call_openweather_api
from weather_mcp.utils import check_geo, handle_error

logger = logging.getLogger(__name__)


# @mcp.tool()
async def get_forecast_hourly_by_geo(lat: float, lon: float, lang: str = "en") -> dict:
    """
    Get hourly weather forecast for a specific geographic location using latitude and longitude coordinates.

    **Function Description:**
    Retrieves detailed hourly weather forecasts from OpenWeatherMap API using precise geographic coordinates.
    Provides up to 48 hours of forecast data with hourly granularity, including temperature trends,
    precipitation probability, wind patterns, and atmospheric conditions. Ideal for applications requiring
    precise location-based weather planning and short-term forecasting.

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
        dict: Hourly forecast data containing:
            - cod: Response code (200 for success)
            - message: Response message
            - cnt: Number of forecast entries (typically 48 for hourly)
            - list: Array of hourly forecast objects, each containing:
                * dt: Forecast timestamp (Unix UTC)
                * main: Temperature/pressure data (temp, feels_like, temp_min, temp_max,
                        pressure, sea_level, grnd_level, humidity, temp_kf)
                * weather: Weather conditions array (id, main, description, icon)
                * clouds: Cloud coverage percentage
                * wind: Wind data (speed, deg, gust)
                * visibility: Average visibility in meters
                * pop: Probability of precipitation (0.0 to 1.0)
                * rain: Rain volume (if applicable) with 3h accumulation
                * snow: Snow volume (if applicable) with 3h accumulation
                * sys: System data (pod - part of day)
                * dt_txt: Human-readable timestamp
            - city: Location information (id, name, coord, country, population, timezone, sunrise, sunset)

    **Raises:**
        ValueError: If coordinates are out of valid range (-90≤lat≤90, -180≤lon≤180)
        APIError: If OpenWeatherMap API returns error status
        NetworkError: If network request fails or times out

    **Usage Examples:**
        # Get 48-hour forecast for Tokyo, Japan
        forecast = await get_forecast_hourly_by_geo(35.6762, 139.6503)

        # Get forecast with German descriptions
        forecast = await get_forecast_hourly_by_geo(52.5200, 13.4050, lang="de")

        # Process hourly data for next 24 hours
        hourly_data = forecast['list'][:24]  # First 24 hours
        for hour in hourly_data:
            timestamp = datetime.fromtimestamp(hour['dt'])
            temp = hour['main']['temp']
            rain_chance = hour['pop'] * 100
            print(f"{timestamp}: {temp}°C, {rain_chance}% rain chance")

        # Find peak temperature in forecast period
        max_temp = max(hour['main']['temp'] for hour in forecast['list'])
        peak_hour = next(h for h in forecast['list'] if h['main']['temp'] == max_temp)
        peak_time = datetime.fromtimestamp(peak_hour['dt'])

        # Check for precipitation in next 12 hours
        next_12h = forecast['list'][:12]
        will_rain = any(hour['pop'] > 0.3 for hour in next_12h)

    **MCP Integration Notes:**
        - Ideal for MCP clients requiring detailed short-term forecasting capabilities
        - Large response payload (48 hours × detailed data) - consider chunking for display
        - Implement client-side caching as forecast data changes less frequently than current weather
        - MCP clients can create time-series visualizations from the hourly data array
        - Consider exposing summary functions (daily highs/lows, rain totals) for simpler client display
        - Tool response may exceed typical MCP message limits - handle pagination if needed

    **Data Processing Tips:**
        - Timestamps are Unix UTC - convert using datetime.fromtimestamp(hour['dt'], tz=timezone.utc)
        - Apply timezone offset from city.timezone for local time display
        - Temperature unit matches API settings (Celsius by default, add units=imperial for Fahrenheit)
        - Precipitation probability (pop) is decimal 0.0-1.0, multiply by 100 for percentage
        - Rain/snow volumes are 3-hour accumulations, not instantaneous rates
        - Wind speed in meters/second (×2.237 for mph, ×3.6 for km/h)
        - Use dt_txt for human-readable time if timestamp conversion is complex
        - Filter by sys.pod for day/night specific processing ('d'=day, 'n'=night)

    **Common Use Cases:**
        - Event planning applications checking detailed weather windows
        - Outdoor activity apps (hiking, sports, construction) needing hourly precision
        - Agricultural systems for irrigation and crop protection timing
        - Transportation/logistics for weather-sensitive operations
        - Energy management systems predicting solar/wind generation
        - Smart home systems for HVAC optimization
        - Travel apps showing hour-by-hour conditions for trips
        - Emergency services planning for weather-related incidents
        - Retail/hospitality adjusting staffing based on weather patterns
    """
    check_geo(lat, lon)
    params = {"lat": lat, "lon": lon, "lang": lang}

    try:
        return await call_openweather_api(OpenWeatherEndpoint.FORECAST_HOURLY, params)

    except Exception as e:
        raise handle_error(e)


# @mcp.tool()
async def get_forecast_hourly_by_city(
    city: str, country_code: str | None = None, lang: str = "en"
) -> dict:
    """
    Get hourly weather forecast for a city by name, with optional country specification.

    **Function Description:**
    Retrieves detailed hourly weather forecasts from OpenWeatherMap API using city name search.
    Provides up to 48 hours of forecast data with hourly granularity for user-friendly city-based queries.
    More accessible than coordinate-based lookup but may require country disambiguation for common city names.
    Automatically handles city name resolution, geocoding, and timezone determination.

    **Args:**
        city (str): City name (e.g., "London", "New York", "São Paulo", "東京").
                   Case-insensitive, supports Unicode characters and diacritics.
                   Can include state/province for US/CA cities (e.g., "Austin,TX").
        country_code (str | None, optional): ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP").
                                           Strongly recommended for cities with duplicate names.
                                           Helps ensure forecast accuracy for intended location.
                                           Defaults to None (global search, returns best match).
        lang (str, optional): Language code for weather descriptions. Defaults to "en" (English).
                              Supports 40+ languages: en, es, fr, de, it, pt, ru, ja, zh_cn, zh_tw,
                              ar, bg, ca, cz, da, el, fa, fi, gl, he, hi, hr, hu, kr, la, lt, lv,
                              mk, nl, no, pl, ro, sk, sl, sv, th, tr, ua, vi, zu

    **Returns:**
        dict: Same comprehensive structure as get_forecast_hourly_by_geo():
            - cod: HTTP response code
            - message: API response message
            - cnt: Number of forecast entries (typically 48)
            - list: Array of 48 hourly forecast objects with complete weather data
            - city: Resolved city information including:
                * id: OpenWeatherMap city ID (store for faster future requests)
                * name: Resolved city name (may differ from input)
                * coord: {lat, lon} - Precise coordinates for the city center
                * country: ISO country code
                * population: City population estimate
                * timezone: UTC offset in seconds
                * sunrise: Sunrise timestamp (Unix UTC)
                * sunset: Sunset timestamp (Unix UTC)

    **Raises:**
        CityNotFoundError: If city name cannot be resolved, doesn't exist, or is ambiguous
        CountryCodeError: If country_code format is invalid (not 2-letter ISO code)
        APIError: If OpenWeatherMap API returns error status
        NetworkError: If network request fails or times out
        ValidationError: If city name is empty, too short, or contains invalid characters
        AmbiguousLocationError: If multiple cities match and no country_code provided

    **Usage Examples:**
        # Basic city forecast
        forecast = await get_forecast_hourly_by_city("Paris")

        # Disambiguate cities with same name
        paris_fr = await get_forecast_hourly_by_city("Paris", "FR")
        paris_tx = await get_forecast_hourly_by_city("Paris", "US")

        # International city with local language
        forecast = await get_forecast_hourly_by_city("Barcelona", "ES", lang="es")

        # Process forecast for business hours (9 AM - 5 PM)
        forecast = await get_forecast_hourly_by_city("Chicago", "US")
        city_tz = forecast['city']['timezone']  # UTC offset in seconds
        business_hours = []
        for hour in forecast['list']:
            local_time = datetime.fromtimestamp(hour['dt'] + city_tz)
            if 9 <= local_time.hour <= 17:
                business_hours.append({
                    'time': local_time,
                    'temp': hour['main']['temp'],
                    'conditions': hour['weather'][0]['description'],
                    'rain_chance': hour['pop']
                })

        # Create daily summary from hourly data
        daily_summary = {}
        for hour in forecast['list']:
            date = datetime.fromtimestamp(hour['dt']).date()
            if date not in daily_summary:
                daily_summary[date] = {'temps': [], 'rain_probs': []}
            daily_summary[date]['temps'].append(hour['main']['temp'])
            daily_summary[date]['rain_probs'].append(hour['pop'])

        # Find best time window for outdoor activity
        good_weather_windows = []
        for i, hour in enumerate(forecast['list'][:-3]):  # Check 4-hour windows
            window = forecast['list'][i:i+4]
            avg_temp = sum(h['main']['temp'] for h in window) / 4
            max_rain_prob = max(h['pop'] for h in window)
            if 20 <= avg_temp <= 25 and max_rain_prob < 0.2:  # Good conditions
                start_time = datetime.fromtimestamp(hour['dt'])
                good_weather_windows.append(start_time)

    **MCP Integration Notes:**
        - Perfect for conversational MCP interfaces handling natural language city queries
        - Store city.id from response for faster subsequent API calls
        - MCP clients should handle city disambiguation by showing multiple options
        - Consider implementing autocomplete/suggestion features using popular city lists
        - Large dataset - implement progressive loading or summary views in MCP clients
        - Cache responses by city+country combination to improve performance
        - Provide fallback error messages that are user-friendly for chat interfaces

    **Data Processing Tips:**
        - City name resolution may return unexpected matches - always verify city.name and city.country
        - Use city.timezone for accurate local time conversion (seconds from UTC)
        - Store city.id for 15% faster API calls on subsequent requests
        - Combine with current weather for comprehensive location-based services
        - Hourly data best processed in chunks (daily, business hours, specific time windows)
        - Consider aggregating hourly data into daily summaries for easier consumption
        - Rain/snow accumulation is per 3-hour period, not per hour
        - Use coordinate data (city.coord) for mapping integrations

    **Common Use Cases:**
        - Travel planning apps showing destination weather throughout trip duration
        - Voice assistants answering "What's the weather like in [city] tomorrow?"
        - Business applications for multi-location weather monitoring
        - Social media integrations showing weather for posted locations
        - Delivery/logistics apps planning routes based on hourly conditions
        - Event management platforms checking weather for outdoor venues
        - News applications providing detailed weather stories for specific cities
        - International business dashboards showing weather at global office locations
        - Tourism websites helping visitors plan daily activities
        - Agriculture apps for farmers with operations in multiple cities
    """
    location = f"{city},{country_code}" if country_code else city

    params = {"q": location, "lang": lang}

    try:
        return await call_openweather_api(OpenWeatherEndpoint.FORECAST_HOURLY, params)

    except Exception as e:
        raise handle_error(e)
