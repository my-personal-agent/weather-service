import logging

from enums.openweather import OpenWeatherEndpoint
from core.http_client import call_openweather_api
from weather_mcp.server import mcp
from weather_mcp.tools.geocoding import get_direct_geo_by_location
from weather_mcp.utils import check_geo, handle_error

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_current_air_pollution_by_geo(lat: float, lon: float) -> dict:
    """
    **Function Description**
    Retrieves current air quality and pollution data for a specific geographic location.
    Returns comprehensive air pollution metrics including Air Quality Index (AQI),
    concentrations of major pollutants (PM2.5, PM10, NO2, SO2, CO, O3), and health recommendations.

    **Args/Returns/Raises**
    Args:
        lat (float): Latitude coordinate in decimal degrees (-90.0 to 90.0)
        lon (float): Longitude coordinate in decimal degrees (-180.0 to 180.0)

    Returns:
        dict: OpenWeatherMap air pollution response containing:
            - coord: Dictionary with lat/lon coordinates
            - list: Array of pollution data objects with:
                - dt: Unix timestamp of the data
                - main: AQI value (1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor)
                - components: Dict of pollutant concentrations in μg/m³
                    - co: Carbon monoxide
                    - no: Nitric oxide
                    - no2: Nitrogen dioxide
                    - o3: Ozone
                    - so2: Sulfur dioxide
                    - pm2_5: Fine particulate matter
                    - pm10: Coarse particulate matter
                    - nh3: Ammonia

    Raises:
        ValueError: If coordinates are outside valid ranges
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur

    **Usage Examples**
    ```python
    # Get current air quality for coordinates
    pollution = await get_current_air_pollution_by_geo(40.7128, -74.0060)  # NYC

    # Extract AQI and main pollutants
    current_data = pollution['list'][0]
    aqi = current_data['main']['aqi']
    pm25 = current_data['components']['pm2_5']
    pm10 = current_data['components']['pm10']

    # Check air quality level
    aqi_levels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    quality = aqi_levels.get(aqi, "Unknown")
    ```

    **MCP Integration Notes**
    - Tool automatically exposed to MCP clients with coordinate validation
    - Coordinates must be passed as numeric types (float/double) from MCP clients
    - Response data includes nested objects that are properly JSON-serialized
    - Error handling follows MCP protocol with appropriate status codes
    - Can be chained with geocoding tools for city-name-based queries
    - Async execution allows concurrent pollution monitoring for multiple locations

    **Data Processing Tips**
    - Always validate coordinates before API calls to prevent errors
    - AQI values are standardized: 1 (best) to 5 (worst) for easy comparison
    - Pollutant concentrations are in μg/m³ - convert to other units if needed
    - Check timestamp (dt) to ensure data freshness
    - Handle missing pollutant data gracefully (some locations may not report all components)
    - Store AQI thresholds for automated alerts and health recommendations
    - Consider averaging multiple nearby locations for area-wide assessments

    **Common Use Cases**
    - Health apps: Alert users about poor air quality conditions
    - Smart home systems: Control air purifiers based on outdoor pollution
    - Urban planning: Monitor pollution levels for policy decisions
    - Travel apps: Provide air quality information for destinations
    - Environmental research: Collect current pollution data for studies
    - Real estate: Inform buyers about air quality in different neighborhoods
    - Fitness apps: Recommend indoor/outdoor activities based on air quality
    """
    check_geo(lat, lon)
    params = {"lat": lat, "lon": lon}
    try:
        return await call_openweather_api(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION, params
        )
    except Exception as e:
        raise handle_error(e)


@mcp.tool()
async def get_current_air_pollution_by_city(
    city: str, state_code: str, country_code: str
) -> dict:
    """
    **Function Description**
    Retrieves current air quality data for a city by name. This is a convenience function
    that combines geocoding and air pollution data retrieval, automatically converting
    city names to coordinates and fetching current pollution information. Provides the
    same data as the coordinate-based function but accepts human-readable location names.

    **Args/Returns/Raises**
    Args:
        city (str): Name of the city (e.g., "New York", "London", "Tokyo")
        state_code (str): State/province code in ISO 3166-2 format (e.g., "NY", "CA", "ENG")
        country_code (str): Country code in ISO 3166-1 alpha-2 format (e.g., "US", "GB", "JP")

    Returns:
        dict: Same format as get_current_air_pollution_by_geo containing:
            - coord: Dictionary with resolved lat/lon coordinates
            - list: Array with current pollution data object
                - dt: Unix timestamp
                - main: Current AQI value (1-5 scale)
                - components: Current pollutant concentrations in μg/m³

    Raises:
        ValueError: If location cannot be found during geocoding
        IndexError: If geocoding returns empty results
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur

    **Usage Examples**
    ```python
    # Get air quality by city name
    pollution = await get_current_air_pollution_by_city("Tokyo", "13", "JP")

    # Extract pollution data
    current_data = pollution['list'][0]
    aqi = current_data['main']['aqi']
    pm25 = current_data['components']['pm2_5']
    no2 = current_data['components']['no2']

    # Multiple cities comparison
    cities = [
        ("London", "ENG", "GB"),
        ("Paris", "IDF", "FR"),
        ("Berlin", "BE", "DE")
    ]

    pollution_data = {}
    for city, state, country in cities:
        data = await get_current_air_pollution_by_city(city, state, country)
        pollution_data[city] = data['list'][0]['main']['aqi']

    # Find cleanest city
    cleanest = min(pollution_data, key=pollution_data.get)
    ```

    **MCP Integration Notes**
    - Automatically chains geocoding and pollution API calls within single MCP tool
    - Error handling covers both geocoding failures and pollution data retrieval
    - Response format identical to coordinate-based function for consistent client handling
    - Ideal for user-facing applications where coordinates are not readily available
    - Caching of geocoding results recommended for repeated city queries
    - Can be used in batch processing workflows for multiple cities

    **Data Processing Tips**
    - Validate city/state/country codes before processing to avoid geocoding failures
    - Handle geocoding errors gracefully with meaningful error messages
    - Cache geocoding results to reduce API calls for repeated city requests
    - Implement fuzzy matching for city names to handle spelling variations
    - Consider time zone differences when displaying timestamps for international cities
    - Store resolved coordinates for future direct API calls to improve performance

    **Common Use Cases**
    - Travel planning: Check air quality for destination cities
    - International business: Monitor air quality across office locations
    - Migration decisions: Compare air quality between potential relocation cities
    - Event planning: Assess air quality for outdoor events in different cities
    - Health management: Track air quality in frequently visited cities
    - Educational tools: Teaching about global air quality patterns
    - News and media: Reporting on air quality conditions in major cities
    """
    geo_data = await get_direct_geo_by_location(city, state_code, country_code, limit=1)

    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
    return await get_current_air_pollution_by_geo(lat, lon)


@mcp.tool()
async def get_forecast_air_pollution_by_geo(lat: float, lon: float) -> dict:
    """
    **Function Description**
    Retrieves air quality forecast data for a specific geographic location.
    Provides predicted air pollution levels and pollutant concentrations for up to 5 days ahead,
    enabling proactive planning for air quality-sensitive activities and health decisions.
    Returns time-series data with hourly predictions for comprehensive pollution forecasting.

    **Args/Returns/Raises**
    Args:
        lat (float): Latitude coordinate in decimal degrees (-90.0 to 90.0)
        lon (float): Longitude coordinate in decimal degrees (-180.0 to 180.0)

    Returns:
        dict: OpenWeatherMap air pollution forecast response containing:
            - coord: Dictionary with lat/lon coordinates
            - list: Array of forecast pollution data objects (typically 5 days, hourly):
                - dt: Unix timestamp for the forecast time
                - main: Predicted AQI value (1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor)
                - components: Dict of predicted pollutant concentrations in μg/m³
                    - co, no, no2, o3, so2, pm2_5, pm10, nh3

    Raises:
        ValueError: If coordinates are outside valid ranges
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur
        ForecastError: If forecast data is unavailable for the location

    **Usage Examples**
    ```python
    from datetime import datetime

    # Get 5-day air quality forecast
    forecast = await get_forecast_air_pollution_by_geo(51.5074, -0.1278)  # London

    # Process forecast data
    for day_data in forecast['list']:
        timestamp = day_data['dt']
        aqi = day_data['main']['aqi']
        pm25 = day_data['components']['pm2_5']
        date = datetime.fromtimestamp(timestamp)
        print(f"{date}: AQI {aqi}, PM2.5 {pm25}μg/m³")

    # Find best air quality day
    best_day = min(forecast['list'], key=lambda x: x['main']['aqi'])
    best_date = datetime.fromtimestamp(best_day['dt'])
    best_aqi = best_day['main']['aqi']

    # Calculate daily averages
    daily_averages = {}
    for item in forecast['list']:
        date_key = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
        if date_key not in daily_averages:
            daily_averages[date_key] = []
        daily_averages[date_key].append(item['main']['aqi'])

    for date, aqi_values in daily_averages.items():
        avg_aqi = sum(aqi_values) / len(aqi_values)
        print(f"{date}: Average AQI {avg_aqi:.1f}")
    ```

    **MCP Integration Notes**
    - Provides time-series data suitable for charting and trend analysis
    - Forecast array can be processed sequentially or in parallel by MCP clients
    - Timestamps are Unix format - convert to local time zones as needed
    - Response size is larger than current data - consider pagination for large datasets
    - Can be combined with weather forecasts for comprehensive environmental planning
    - Enables predictive workflows in MCP automation systems

    **Data Processing Tips**
    - Convert Unix timestamps to readable dates for user interfaces
    - Implement trend analysis to identify improving/worsening air quality patterns
    - Cache forecast data to reduce API calls (data updates every few hours)
    - Compare forecasted vs actual values to assess forecast accuracy
    - Use forecast data to trigger automated actions (alerts, device control)
    - Consider seasonal patterns when interpreting forecast trends
    - Filter forecast data by specific pollutants based on health conditions
    - Aggregate hourly data into daily summaries for simplified presentation

    **Common Use Cases**
    - Health planning: Schedule outdoor activities for days with better air quality
    - Event management: Plan outdoor events based on predicted air quality
    - Smart city systems: Optimize traffic patterns based on pollution forecasts
    - Agricultural planning: Timing of agricultural activities based on air quality
    - HVAC optimization: Pre-adjust building ventilation based on forecasts
    - Travel planning: Choose travel dates with better air quality
    - Environmental compliance: Predict when pollution levels may exceed thresholds
    - Sports scheduling: Plan outdoor sports events for optimal air quality conditions
    """
    check_geo(lat, lon)
    params = {"lat": lat, "lon": lon}
    try:
        return await call_openweather_api(
            OpenWeatherEndpoint.FORECAST_AIR_POLLUTION, params
        )
    except Exception as e:
        raise handle_error(e)


@mcp.tool()
async def get_forecast_air_pollution_by_city(
    city: str, state_code: str, country_code: str
) -> dict:
    """
    **Function Description**
    Retrieves air quality forecast data for a city by name within a 5-day timeframe.
    Combines geocoding with pollution forecasting to provide predicted air quality
    using human-readable city names instead of coordinates. Offers the same comprehensive
    forecast data as the coordinate-based function with automatic location resolution.

    **Args/Returns/Raises**
    Args:
        city (str): Name of the city (e.g., "Beijing", "Mumbai", "Los Angeles")
        state_code (str): State/province code in ISO 3166-2 format (e.g., "BJ", "MH", "CA")
        country_code (str): Country code in ISO 3166-1 alpha-2 format (e.g., "CN", "IN", "US")

    Returns:
        dict: Same format as get_forecast_air_pollution_by_geo containing:
            - coord: Dictionary with resolved lat/lon coordinates
            - list: Array of forecast pollution data objects (5 days, hourly)
                - dt: Unix timestamp for each forecast point
                - main: Predicted AQI values (1-5 scale)
                - components: Predicted pollutant concentrations in μg/m³

    Raises:
        ValueError: If location cannot be found during geocoding
        IndexError: If geocoding returns empty results
        APIError: If any API request fails
        NetworkError: If network connectivity issues occur
        ForecastError: If forecast data is unavailable

    **Usage Examples**
    ```python
    from datetime import datetime

    # Get forecast by city name
    forecast = await get_forecast_air_pollution_by_city("Mumbai", "MH", "IN")

    # Find worst air quality day
    worst_day = max(forecast['list'], key=lambda x: x['main']['aqi'])
    worst_date = datetime.fromtimestamp(worst_day['dt'])
    worst_pm25 = worst_day['components']['pm2_5']

    # Compare multiple cities' forecasts
    cities_to_check = [
        ("Delhi", "DL", "IN"),
        ("Bangkok", "10", "TH"),
        ("Jakarta", "JK", "ID")
    ]

    city_forecasts = {}
    for city, state, country in cities_to_check:
        forecast = await get_forecast_air_pollution_by_city(city, state, country)
        # Get average AQI for next 24 hours
        next_24h = forecast['list'][:24]  # First 24 hourly forecasts
        avg_aqi = sum(item['main']['aqi'] for item in next_24h) / len(next_24h)
        city_forecasts[city] = avg_aqi

    # Find city with best air quality forecast
    best_city = min(city_forecasts, key=city_forecasts.get)
    ```

    **MCP Integration Notes**
    - Seamlessly combines two API operations (geocoding + forecast) in single MCP tool
    - Consistent response format with coordinate-based function for unified client handling
    - Automatic error propagation from geocoding and forecast API calls
    - Suitable for user-facing applications where city names are primary input
    - Enables batch processing of multiple cities with concurrent execution
    - Integrates well with scheduling and notification systems

    **Data Processing Tips**
    - Validate location parameters before processing to minimize API failures
    - Cache geocoding results for repeated city requests to improve performance
    - Implement retry logic for geocoding failures due to ambiguous city names
    - Process forecast arrays efficiently for large-scale city comparisons
    - Convert timestamps to local time zones for each city for accurate interpretation
    - Aggregate hourly forecasts into daily/weekly summaries for easier consumption
    - Store city-coordinate mappings to bypass geocoding in future requests

    **Common Use Cases**
    - Travel advisories: Forecast air quality for destination cities
    - Business continuity: Plan operations based on air quality predictions across locations
    - Health tourism: Choose destinations with favorable air quality forecasts
    - Supply chain management: Anticipate air quality impacts on logistics operations
    - Educational research: Study predicted air quality patterns across global cities
    - Media and journalism: Report on upcoming air quality conditions in major cities
    - International events: Plan conferences, sports events based on air quality forecasts
    """
    geo_data = await get_direct_geo_by_location(city, state_code, country_code, limit=1)

    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
    return await get_forecast_air_pollution_by_geo(lat, lon)


@mcp.tool()
async def get_historical_air_pollution_by_geo(
    lat: float, lon: float, start: int, end: int
) -> dict:
    """
    **Function Description**
    Retrieves historical air quality and pollution data for a specific geographic location
    within a specified time range. Provides access to past air pollution measurements
    for trend analysis, research, compliance reporting, and environmental studies.
    Maximum time range is 1 year per request with hourly data resolution.

    **Args/Returns/Raises**
    Args:
        lat (float): Latitude coordinate in decimal degrees (-90.0 to 90.0)
        lon (float): Longitude coordinate in decimal degrees (-180.0 to 180.0)
        start (int): Start date as Unix timestamp (inclusive)
        end (int): End date as Unix timestamp (inclusive, max 1 year from start)

    Returns:
        dict: OpenWeatherMap historical air pollution response containing:
            - coord: Dictionary with lat/lon coordinates
            - list: Array of historical pollution data objects:
                - dt: Unix timestamp of the measurement
                - main: Historical AQI value (1-5 scale)
                - components: Dict of pollutant concentrations in μg/m³
                    - co, no, no2, o3, so2, pm2_5, pm10, nh3

    Raises:
        ValueError: If coordinates are invalid or time range exceeds 1 year limit
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur
        HistoricalDataError: If historical data is unavailable for the specified period
        TimeRangeError: If start date is after end date or range is too large

    **Usage Examples**
    ```python
    from datetime import datetime, timedelta
    import statistics

    # Get last 30 days of air quality data
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=30)).timestamp())

    historical = await get_historical_air_pollution_by_geo(
        40.7128, -74.0060,  # NYC coordinates
        start_time, end_time
    )

    # Analyze trends
    aqi_values = [item['main']['aqi'] for item in historical['list']]
    avg_aqi = statistics.mean(aqi_values)
    median_aqi = statistics.median(aqi_values)

    # Monthly pollution analysis
    from collections import defaultdict
    monthly_data = defaultdict(list)
    for item in historical['list']:
        month = datetime.fromtimestamp(item['dt']).strftime('%Y-%m')
        monthly_data[month].append(item['components']['pm2_5'])

    monthly_averages = {
        month: statistics.mean(values)
        for month, values in monthly_data.items()
    }

    # Find pollution peaks
    max_pollution = max(historical['list'], key=lambda x: x['components']['pm2_5'])
    peak_date = datetime.fromtimestamp(max_pollution['dt'])
    peak_pm25 = max_pollution['components']['pm2_5']
    ```

    **MCP Integration Notes**
    - Time range limited to 1 year maximum per API call for performance
    - Large datasets may require pagination or chunking for efficient processing
    - Historical data is ideal for batch processing and analytics workflows
    - Timestamps require conversion to local time zones for user presentation
    - Can be integrated with data visualization tools for trend charts
    - Suitable for automated report generation and compliance monitoring
    - Memory-intensive for long time ranges - consider streaming for large datasets

    **Data Processing Tips**
    - Validate time range before API calls (start < end, max 1 year span)
    - Handle missing data points gracefully in time series analysis
    - Implement data aggregation for daily/weekly/monthly summaries
    - Use statistical analysis to identify pollution trends and patterns
    - Compare historical data with current/forecast data for comprehensive analysis
    - Consider seasonal adjustments when analyzing long-term trends
    - Export data to CSV/Excel formats for external analysis tools
    - Implement data quality checks for outliers and anomalies
    - Use moving averages to smooth out short-term fluctuations

    **Common Use Cases**
    - Environmental research: Long-term pollution trend analysis and climate studies
    - Compliance reporting: Generate historical pollution reports for regulatory authorities
    - Health studies: Correlate air quality data with health outcomes and epidemiological research
    - Urban planning: Analyze pollution patterns for development and zoning decisions
    - Insurance assessment: Evaluate environmental risk factors for property and health insurance
    - Real estate analytics: Provide historical air quality data for property valuations
    - Academic research: Environmental science and public health policy studies
    - Policy evaluation: Assess effectiveness of pollution control measures over time
    """
    check_geo(lat, lon)
    params = {"lat": lat, "lon": lon, "start": start, "end": end}
    try:
        return await call_openweather_api(
            OpenWeatherEndpoint.HISTORICAL_AIR_POLLUTION, params
        )
    except Exception as e:
        raise handle_error(e)


@mcp.tool()
async def get_historical_air_pollution_by_city(
    city: str, state_code: str, country_code: str, start: int, end: int
) -> dict:
    """
    **Function Description**
    Retrieves historical air quality data for a city by name within a specified time range.
    Combines geocoding with historical pollution data retrieval to provide past air quality
    measurements using human-readable city names instead of coordinates. Offers the same
    comprehensive historical analysis capabilities with automatic location resolution.

    **Args/Returns/Raises**
    Args:
        city (str): Name of the city (e.g., "Delhi", "Mexico City", "São Paulo")
        state_code (str): State/province code in ISO 3166-2 format (e.g., "DL", "CDMX", "SP")
        country_code (str): Country code in ISO 3166-1 alpha-2 format (e.g., "IN", "MX", "BR")
        start (int): Start date as Unix timestamp (inclusive)
        end (int): End date as Unix timestamp (inclusive, max 1 year from start)

    Returns:
        dict: Same format as get_historical_air_pollution_by_geo containing:
            - coord: Dictionary with resolved lat/lon coordinates
            - list: Array of historical pollution measurements
                - dt: Unix timestamp of each measurement
                - main: Historical AQI values (1-5 scale)
                - components: Historical pollutant concentrations in μg/m³

    Raises:
        ValueError: If location cannot be found or time range is invalid
        IndexError: If geocoding returns empty results
        APIError: If any API request fails
        NetworkError: If network connectivity issues occur
        TimeRangeError: If time range exceeds 1 year or start > end

    **Usage Examples**
    ```python
    from datetime import datetime, timedelta
    import json

    # Get last 90 days for a specific city
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=90)).timestamp())

    historical = await get_historical_air_pollution_by_city(
        "Beijing", "BJ", "CN", start_time, end_time
    )

    # Calculate average PM2.5 levels
    pm25_values = [item['components']['pm2_5'] for item in historical['list']]
    avg_pm25 = sum(pm25_values) / len(pm25_values)

    # Compare multiple cities over same period
    cities_to_analyze = [
        ("Beijing", "BJ", "CN"),
        ("New Delhi", "DL", "IN"),
        ("Los Angeles", "CA", "US")
    ]

    city_comparisons = {}
    for city, state, country in cities_to_analyze:
        data = await get_historical_air_pollution_by_city(
            city, state, country, start_time, end_time
        )

        # Calculate city statistics
        aqi_values = [item['main']['aqi'] for item in data['list']]
        pm25_values = [item['components']['pm2_5'] for item in data['list']]

        city_comparisons[city] = {
            'avg_aqi': sum(aqi_values) / len(aqi_values),
            'avg_pm25': sum(pm25_values) / len(pm25_values),
            'worst_aqi': max(aqi_values),
            'best_aqi': min(aqi_values)
        }

    # Export results
    with open('city_air_quality_comparison.json', 'w') as f:
        json.dump(city_comparisons, f, indent=2)
    ```

    **MCP Integration Notes**
    - Automatically chains geocoding and historical data retrieval in single MCP operation
    - Response format consistent with coordinate-based function for unified processing
    - Error handling covers both geocoding and historical data retrieval failures
    - Suitable for comparative analysis workflows across multiple cities
    - Enables batch processing with concurrent execution for multiple cities
    - Integrates with data export and visualization systems for reporting

    **Data Processing Tips**
    - Validate location and time parameters before processing to prevent API failures
    - Cache geocoding results for repeated city analysis to improve performance
    - Implement data validation to handle cities with limited historical data availability
    - Use efficient data structures for large-scale multi-city comparisons
    - Consider time zone differences when analyzing international cities
    - Implement data export capabilities for integration with analysis tools
    - Store city-coordinate mappings to optimize future historical requests
    - Use statistical sampling for very large datasets to manage memory usage

    **Common Use Cases**
    - International environmental studies: Compare pollution trends across global cities
    - Migration planning: Analyze historical air quality for relocation decisions
    - Business location analysis: Evaluate air quality history for facility placement
    - Tourism impact assessment: Study seasonal air quality patterns in destination cities
    - Policy research: Compare effectiveness of environmental policies across cities
    - Health outcome correlation: Link historical air quality with public health data
    - Climate change research: Study long-term pollution trends in urban areas
    - Investment analysis: Assess environmental factors for real estate and business investments
    """
    geo_data = await get_direct_geo_by_location(city, state_code, country_code, limit=1)

    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
    return await get_historical_air_pollution_by_geo(lat, lon, start, end)
