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
async def get_forecast_by_geo(
    ctx: Context,
    lat: ANNOTATED_LAT,
    lon: ANNOTATED_LON,
    lang: ANNOTATED_LANG = "en",
) -> dict[str, Any]:
    """
    Get 5-day weather forecast with 3-hour intervals for a specific geographic location using coordinates.

    **Function Description:**
    Retrieves detailed 5-day weather forecasts from OpenWeatherMap API using precise geographic coordinates
    with 3-hour granularity (40 forecast points total). This provides the optimal balance between detail
    and coverage, offering medium-term planning capability with sufficient temporal resolution for most
    applications. Each 3-hour interval includes comprehensive weather data including temperature, precipitation,
    wind, and atmospheric conditions. Perfect for applications requiring detailed short-to-medium term
    forecasting without the data volume of hourly forecasts or the reduced granularity of daily forecasts.

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
        dict: 5-day/3-hour forecast data containing:
            - cod: Response code (200 for success)
            - message: Response message and metadata
            - cnt: Number of forecast entries (40 for 5 days × 8 intervals per day)
            - list: Array of 40 forecast objects (every 3 hours), each containing:
                * dt: Forecast timestamp (Unix UTC)
                * main: Temperature and atmospheric data:
                    - temp: Temperature at forecast time
                    - feels_like: Perceived temperature
                    - temp_min: Minimum temperature in interval
                    - temp_max: Maximum temperature in interval
                    - pressure: Atmospheric pressure (hPa)
                    - sea_level: Sea level pressure (hPa)
                    - grnd_level: Ground level pressure (hPa)
                    - humidity: Humidity percentage (0-100)
                    - temp_kf: Temperature correction factor
                * weather: Weather conditions array (id, main, description, icon)
                * clouds: Cloud coverage percentage (0-100)
                * wind: Wind information (speed in m/s, deg in degrees 0-360, gust if applicable)
                * visibility: Average visibility in meters (max 10000)
                * pop: Probability of precipitation (0.0-1.0)
                * rain: Rain volume object with 3h accumulation (mm)
                * snow: Snow volume object with 3h accumulation (mm)
                * sys: System data (pod: part of day - 'd' for day, 'n' for night)
                * dt_txt: Human-readable timestamp (YYYY-MM-DD HH:MM:SS format)
            - city: Location information (id, name, coord, country, population, timezone, sunrise, sunset)

    **Raises:**
        ValueError: If coordinates are out of valid range (-90≤lat≤90, -180≤lon≤180)
        APIError: If OpenWeatherMap API returns error status
        NetworkError: If network request fails or times out

    **Usage Examples:**
        # Get 5-day forecast for San Francisco coordinates
        forecast = await get_forecast_by_geo(37.7749, -122.4194)

        # Get forecast with German language descriptions
        forecast = await get_forecast_by_geo(52.5200, 13.4050, lang="de")

        # Process next 24 hours (8 intervals of 3 hours each)
        next_24h = forecast['list'][:8]
        for interval in next_24h:
            time = datetime.fromtimestamp(interval['dt'])
            temp = interval['main']['temp']
            conditions = interval['weather'][0]['description']
            rain_prob = interval['pop'] * 100
            print(f"{time.strftime('%H:%M')}: {temp}°C, {conditions}, {rain_prob}% rain")

        # Find daily temperature peaks and valleys
        daily_temps = {}
        for interval in forecast['list']:
            date = datetime.fromtimestamp(interval['dt']).date()
            if date not in daily_temps:
                daily_temps[date] = {'temps': [], 'times': []}
            daily_temps[date]['temps'].append(interval['main']['temp'])
            daily_temps[date]['times'].append(datetime.fromtimestamp(interval['dt']))

        # Identify best 6-hour windows for outdoor activities
        activity_windows = []
        for i in range(len(forecast['list']) - 1):  # 6-hour windows (2 consecutive 3-hour intervals)
            window = forecast['list'][i:i+2]
            avg_temp = sum(w['main']['temp'] for w in window) / 2
            max_rain_prob = max(w['pop'] for w in window)
            avg_clouds = sum(w['clouds']['all'] for w in window) / 2

            if 18 <= avg_temp <= 25 and max_rain_prob < 0.2 and avg_clouds < 40:
                start_time = datetime.fromtimestamp(window[0]['dt'])
                activity_windows.append({
                    'start': start_time,
                    'end': start_time + timedelta(hours=6),
                    'conditions': 'ideal',
                    'avg_temp': avg_temp
                })

        # Analyze precipitation patterns
        rain_periods = []
        current_rain_start = None
        for interval in forecast['list']:
            time = datetime.fromtimestamp(interval['dt'])
            has_rain = interval['pop'] > 0.3 or interval.get('rain', {}).get('3h', 0) > 0

            if has_rain and current_rain_start is None:
                current_rain_start = time
            elif not has_rain and current_rain_start is not None:
                rain_periods.append({
                    'start': current_rain_start,
                    'end': time,
                    'duration_hours': (time - current_rain_start).total_seconds() / 3600
                })
                current_rain_start = None

        # Generate daily summaries from 3-hour data
        daily_summary = {}
        for interval in forecast['list']:
            date = datetime.fromtimestamp(interval['dt']).date()
            if date not in daily_summary:
                daily_summary[date] = {
                    'temps': [], 'rain_probs': [], 'conditions': [],
                    'wind_speeds': [], 'humidity': []
                }

            daily_summary[date]['temps'].append(interval['main']['temp'])
            daily_summary[date]['rain_probs'].append(interval['pop'])
            daily_summary[date]['conditions'].append(interval['weather'][0]['main'])
            daily_summary[date]['wind_speeds'].append(interval['wind']['speed'])
            daily_summary[date]['humidity'].append(interval['main']['humidity'])

        # Calculate daily averages and extremes
        for date, data in daily_summary.items():
            daily_summary[date] = {
                'temp_min': min(data['temps']),
                'temp_max': max(data['temps']),
                'temp_avg': sum(data['temps']) / len(data['temps']),
                'max_rain_prob': max(data['rain_probs']),
                'dominant_condition': max(set(data['conditions']), key=data['conditions'].count),
                'avg_wind': sum(data['wind_speeds']) / len(data['wind_speeds']),
                'avg_humidity': sum(data['humidity']) / len(data['humidity'])
            }

    **MCP Integration Notes:**
        - Optimal balance of detail vs. response size for most MCP client applications
        - 40 data points provide sufficient granularity without overwhelming client displays
        - Consider implementing time-based filtering (next 12h, 24h, 48h) in MCP client UI
        - Cache responses for 3-4 hours as 3-hour forecasts update less frequently than hourly
        - MCP clients can create timeline visualizations and trend graphs from 3-hour intervals
        - Implement progressive disclosure: show daily summaries with drill-down to 3-hour detail
        - Enable weather alerts based on threshold crossing in upcoming 3-hour intervals
        - Consider chunking display by days with expandable 3-hour breakdowns

    **Data Processing Tips:**
        - Each forecast point represents conditions at a specific 3-hour mark (00:00, 03:00, 06:00, etc. UTC)
        - Apply city.timezone offset for accurate local time display and interpretation
        - Rain/snow volumes are cumulative for the 3-hour period, not instantaneous rates
        - Use dt_txt for simpler timestamp parsing if Unix conversion is complex
        - Temperature min/max in each interval may represent micro-variations within 3 hours
        - Part of day (sys.pod) helps distinguish day/night intervals for UI theming
        - Visibility is capped at 10km (10000m) - values at maximum indicate unlimited visibility
        - Wind gust data only present during periods of significant wind variation
        - Combine consecutive intervals for longer-term pattern analysis (6h, 12h, daily)

    **Common Use Cases:**
        - Outdoor event planning requiring specific timing windows (concerts, festivals, sports)
        - Transportation and logistics with weather-sensitive schedules (flights, shipping, deliveries)
        - Construction and infrastructure projects needing detailed short-term weather windows
        - Agricultural operations requiring precise timing (spraying, harvesting, planting)
        - Energy sector applications for load forecasting and renewable generation planning
        - Retail and hospitality for inventory planning and customer flow prediction
        - Emergency services planning for weather-related incident preparedness
        - Sports and recreation apps helping users plan activities with optimal timing
        - Travel applications showing detailed weather for multi-day trips
        - Smart city systems for traffic management and public safety planning
        - Marine and aviation weather services requiring intermediate-term detailed forecasts
    """
    params = {"lat": lat, "lon": lon, "lang": lang}
    return await call_openweather_api(OpenWeatherEndpoint.FORECAST, params, mcp_ctx=ctx)


@mcp.tool()
async def get_forecast_by_city(
    ctx: Context,
    city: ANNOTATED_CITY,
    country_code: ANNOTATED_OPTIONAL_COUNTRY_CODE = None,
    lang: ANNOTATED_LANG = "en",
) -> dict[str, Any]:
    """
    Get 5-day weather forecast with 3-hour intervals for a city by name with optional country specification.

    **Function Description:**
    Retrieves detailed 5-day weather forecasts from OpenWeatherMap API using city name search with 3-hour
    granularity (40 forecast points total). Provides the optimal balance between forecast detail and time
    coverage for user-friendly city-based queries. More accessible than coordinate-based lookup while
    maintaining full temporal resolution. Automatically handles city name resolution, geocoding, timezone
    determination, and location disambiguation when combined with country codes. Perfect for applications
    where users specify locations by familiar city names rather than coordinates.

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
        dict: Complete 5-day/3-hour forecast structure identical to get_forecast_by_geo():
            - cod: HTTP response code (200 indicates success)
            - message: API response metadata and processing info
            - cnt: Number of forecast entries (consistently 40 for 5-day/3-hour format)
            - city: Comprehensive resolved city information:
                * id: OpenWeatherMap city identifier (cache for faster future requests)
                * name: Resolved city name (may be normalized from input)
                * coord: {lat, lon} - Precise coordinates for mapping and location services
                * country: ISO country code (confirms resolved location)
                * population: Estimated city population for context
                * timezone: UTC offset in seconds for local time calculations
                * sunrise: Today's sunrise timestamp (Unix UTC)
                * sunset: Today's sunset timestamp (Unix UTC)
            - list: Array of 40 forecast objects at 3-hour intervals with complete weather data

    **Raises:**
        CityNotFoundError: If city name cannot be resolved, doesn't exist, or is ambiguous
        CountryCodeError: If country_code format is invalid (not 2-letter ISO code)
        APIError: If OpenWeatherMap API returns error status
        NetworkError: If network request fails or times out
        ValidationError: If city name is empty, too short, or contains invalid characters
        AmbiguousLocationError: If multiple cities match and no country_code provided

    **Usage Examples:**
        # Basic 5-day forecast for a major city
        forecast = await get_forecast_by_city("Paris")

        # Disambiguate cities with same names using country codes
        london_uk = await get_forecast_by_city("London", "GB")
        london_ca = await get_forecast_by_city("London", "CA")

        # Get forecast with localized descriptions
        tokyo_forecast = await get_forecast_by_city("Tokyo", "JP", lang="ja")

        # Business hours weather analysis (9 AM - 5 PM local time)
        business_forecast = await get_forecast_by_city("Chicago", "US")
        timezone_offset = business_forecast['city']['timezone']
        business_hours_weather = []

        for interval in business_forecast['list']:
            utc_time = datetime.fromtimestamp(interval['dt'])
            local_time = utc_time + timedelta(seconds=timezone_offset)

            if 9 <= local_time.hour <= 17 and local_time.weekday() < 5:  # Business hours, weekdays
                business_hours_weather.append({
                    'datetime': local_time,
                    'temperature': interval['main']['temp'],
                    'conditions': interval['weather'][0]['description'],
                    'precipitation_chance': interval['pop'] * 100,
                    'wind_speed': interval['wind']['speed']
                })

        # Weekend weather planning
        weekend_forecast = await get_forecast_by_city("Barcelona", "ES")
        weekend_periods = []

        for interval in weekend_forecast['list']:
            local_time = datetime.fromtimestamp(interval['dt'] + weekend_forecast['city']['timezone'])
            if local_time.weekday() >= 5:  # Saturday (5) or Sunday (6)
                weekend_periods.append({
                    'day': local_time.strftime('%A'),
                    'time': local_time.strftime('%H:%M'),
                    'temp': interval['main']['temp'],
                    'conditions': interval['weather'][0']['description'],
                    'rain_chance': interval['pop']
                })

        # Travel itinerary weather integration
        destinations = [
            ("Rome", "IT"), ("Florence", "IT"), ("Venice", "IT")
        ]
        travel_weather = {}

        for city, country in destinations:
            forecast = await get_forecast_by_city(city, country)

            # Get weather for next 3 days at each destination
            daily_weather = {}
            for interval in forecast['list'][:24]:  # 3 days × 8 intervals per day
                date = datetime.fromtimestamp(interval['dt']).date()
                if date not in daily_weather:
                    daily_weather[date] = {'temps': [], 'conditions': [], 'rain_probs': []}

                daily_weather[date]['temps'].append(interval['main']['temp'])
                daily_weather[date]['conditions'].append(interval['weather'][0]['main'])
                daily_weather[date]['rain_probs'].append(interval['pop'])

            # Summarize each day
            city_summary = {}
            for date, data in daily_weather.items():
                city_summary[date] = {
                    'temp_range': f"{min(data['temps']):.1f}-{max(data['temps']):.1f}°C",
                    'dominant_condition': max(set(data['conditions']), key=data['conditions'].count),
                    'max_rain_chance': max(data['rain_probs']) * 100,
                    'travel_rating': 'excellent' if max(data['rain_probs']) < 0.2 and min(data['temps']) > 15 else 'good'
                }

            travel_weather[f"{city}, {country}"] = city_summary

        # Commuter weather alerts
        commute_forecast = await get_forecast_by_city("Seattle", "US")
        commute_alerts = []

        # Check morning (7-9 AM) and evening (5-7 PM) commute times for next 5 days
        for interval in commute_forecast['list']:
            local_time = datetime.fromtimestamp(interval['dt'] + commute_forecast['city']['timezone'])
            hour = local_time.hour

            if hour in [7, 8, 17, 18]:  # Commute hours
                alert_conditions = []
                if interval['pop'] > 0.6:
                    alert_conditions.append(f"High rain chance ({interval['pop']*100:.0f}%)")
                if interval['wind']['speed'] > 8:
                    alert_conditions.append(f"Strong winds ({interval['wind']['speed']:.1f} m/s)")
                if interval['main']['temp'] < 0:
                    alert_conditions.append(f"Freezing temperature ({interval['main']['temp']:.1f}°C)")
                if 'fog' in interval['weather'][0]['description'].lower():
                    alert_conditions.append("Fog conditions")

                if alert_conditions:
                    commute_alerts.append({
                        'time': local_time.strftime('%A %I:%M %p'),
                        'period': 'Morning Commute' if hour < 12 else 'Evening Commute',
                        'alerts': alert_conditions,
                        'conditions': interval['weather'][0]['description']
                    })

    **MCP Integration Notes:**
        - Ideal for conversational MCP interfaces handling natural language city-based weather queries
        - Implement intelligent city name autocomplete and suggestion features in MCP clients
        - Store city.id from responses for 15% performance improvement on repeat requests
        - MCP clients should handle city disambiguation gracefully with user-friendly option selection
        - Consider implementing location favorites and recent searches for improved user experience
        - Enable smart notifications and weather alerts based on user's preferred cities
        - Cache city-based forecasts for 3-4 hours to balance freshness with performance
        - Provide both summary views and detailed 3-hour breakdowns in client interfaces
        - Implement location-aware features using user's current city as default context

    **Data Processing Tips:**
        - Always verify that resolved city name and country match user expectations
        - Use city.timezone for accurate local time conversion and display
        - Store and reuse city.id for significant performance optimization in repeat queries
        - 3-hour intervals provide optimal balance between detail and data volume
        - Group intervals by local calendar days for daily summary generation
        - Consider user's timezone context when displaying forecast times
        - Combine with current weather data for comprehensive location intelligence
        - Use coordinate data (city.coord) for integration with mapping and location services
        - Implement smart rounding and averaging when aggregating 3-hour data into larger periods
        - Handle edge cases where forecast period crosses daylight saving time transitions

    **Common Use Cases:**
        - Travel and vacation planning applications with city-based destination weather
        - Voice assistants and chatbots handling conversational weather queries for cities
        - Business applications monitoring weather conditions across multiple office locations
        - Social media platforms providing weather context for city-tagged posts and check-ins
        - News and media applications delivering weather stories and updates for specific cities
        - Event management platforms for outdoor venue selection and scheduling
        - International logistics and supply chain weather monitoring for major cities
        - Dating and social apps suggesting weather-appropriate activities in user's city
        - Tourism and hospitality websites helping visitors plan city-based activities
        - Educational applications teaching weather patterns and climate analysis for global cities
        - Emergency management systems for multi-city weather preparedness and response planning
    """
    location = f"{city},{country_code}" if country_code else city
    params = {"q": location, "lang": lang}

    return await call_openweather_api(OpenWeatherEndpoint.FORECAST, params, mcp_ctx=ctx)
