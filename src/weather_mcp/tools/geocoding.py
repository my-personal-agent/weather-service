import logging

from enums.openweather import OpenWeatherEndpoint
from core.http_client import call_openweather_api
from weather_mcp.server import mcp
from weather_mcp.utils import check_geo, handle_error

logger = logging.getLogger(__name__)


def check_limit(limit: int | None):
    """
    Validate the limit parameter for geocoding requests.
    Args:
        limit (int | None): The limit value to check. If None, no validation is performed.
    Raises:
        ValueError: If limit is not None and is outside the range 1 to 5.
    """
    if limit is not None and (limit < 1 or limit > 5):
        raise ValueError("Limit must be between 1 and 5")


@mcp.tool()
async def get_direct_geo_by_location(
    city: str, state_code: str, country_code: str, limit: int | None = None
) -> dict:
    """
    **Function Description**
    Retrieves geographical coordinates and location data for a specified city using direct geocoding.
    Converts human-readable location names into precise latitude/longitude coordinates along with
    additional metadata like country, state, and local names in multiple languages.

    **Args/Returns/Raises**
    Args:
        city (str): Name of the city to geocode (e.g., "New York", "London", "Tokyo")
        state_code (str): State/province code in ISO 3166-2 format (e.g., "NY", "CA", "ON")
        country_code (str): Country code in ISO 3166-1 alpha-2 format (e.g., "US", "GB", "JP")
        limit (int, optional): Maximum number of results to return (default: API default, typically 5)

    Returns:
        dict: OpenWeatherMap geocoding response containing:
            - name: City name
            - lat: Latitude coordinate
            - lon: Longitude coordinate
            - country: Country code
            - state: State/province name
            - local_names: Dictionary of localized names

    Raises:
        ValueError: If limit exceeds maximum allowed value or location parameters are invalid
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur

    **Usage Examples**
    ```python
    # Basic city lookup
    result = await get_direct_geo_by_location("New York", "NY", "US")

    # Limited results
    result = await get_direct_geo_by_location("London", "ENG", "GB", limit=1)

    # International location
    result = await get_direct_geo_by_location("Tokyo", "13", "JP", limit=3)

    # Extract coordinates
    coords = result[0] if result else None
    if coords:
        lat, lon = coords['lat'], coords['lon']
    ```

    **MCP Integration Notes**
    - This tool is automatically exposed to MCP clients when the server starts
    - Tool name in MCP: "get_direct_geo_by_location"
    - All parameters are passed as JSON objects from MCP clients
    - Return values are automatically serialized to JSON for MCP transport
    - Error handling follows MCP protocol standards with proper error codes
    - Async operation allows non-blocking execution in MCP server context

    **Data Processing Tips**
    - Always check if the returned list is non-empty before accessing results
    - Results are ordered by relevance/accuracy from the geocoding service
    - Use `limit=1` when you only need the most accurate match
    - Handle multiple results by presenting options to users or using additional filtering
    - Cache results when possible to reduce API calls for repeated locations
    - Validate coordinate ranges: lat (-90 to 90), lon (-180 to 180)

    **Common Use Cases**
    - Weather application: Convert user-entered cities to coordinates for weather data
    - Logistics: Geocode shipping addresses for route optimization
    - Analytics: Standardize location data in business intelligence systems
    - Travel apps: Convert destination names to mappable coordinates
    - Real estate: Normalize property location data
    - Emergency services: Quick location lookup for dispatch systems
    """
    check_limit(limit)

    params = {"q": f"{city},{state_code},{country_code}"}
    if limit is not None:
        params["limit"] = str(limit)

    try:
        return await call_openweather_api(OpenWeatherEndpoint.DIRECT_GEOCODING, params)
    except Exception as e:
        raise handle_error(e)


@mcp.tool()
async def get_direct_geo_by_coordinates(
    lat: float, lon: float, limit: int | None = None
) -> dict:
    """
    **Function Description**
    Performs reverse geocoding to convert latitude/longitude coordinates into human-readable
    location information. Returns detailed location data including city, state, country,
    and localized names for the specified coordinates.

    **Args/Returns/Raises**
    Args:
        lat (float): Latitude coordinate in decimal degrees (-90.0 to 90.0)
        lon (float): Longitude coordinate in decimal degrees (-180.0 to 180.0)
        limit (int, optional): Maximum number of location results to return

    Returns:
        dict: OpenWeatherMap reverse geocoding response containing:
            - name: Primary location name (usually city/town)
            - lat: Exact latitude (may differ slightly from input)
            - lon: Exact longitude (may differ slightly from input)
            - country: Country code (ISO 3166-1 alpha-2)
            - state: State/province name
            - local_names: Localized names in various languages

    Raises:
        ValueError: If coordinates are outside valid ranges or limit is invalid
        APIError: If OpenWeatherMap API request fails
        NetworkError: If network connectivity issues occur
        GeolocationError: If coordinates don't correspond to any known location

    **Usage Examples**
    ```python
    # Reverse geocode coordinates
    result = await get_direct_geo_by_coordinates(40.7128, -74.0060)  # NYC

    # With result limit
    result = await get_direct_geo_by_coordinates(51.5074, -0.1278, limit=1)  # London

    # Process results
    if result:
        location = result[0]
        print(f"Location: {location['name']}, {location['state']}, {location['country']}")

    # GPS coordinates from mobile device
    user_lat, user_lon = get_device_location()
    nearby_places = await get_direct_geo_by_coordinates(user_lat, user_lon, limit=5)
    ```

    **MCP Integration Notes**
    - Tool automatically registered with MCP server on startup
    - Coordinates should be passed as numeric types (float/double) from MCP clients
    - JSON serialization preserves coordinate precision for accurate reverse geocoding
    - Error responses follow MCP error handling conventions
    - Integrates seamlessly with other location-based MCP tools
    - Supports batch processing when called multiple times asynchronously

    **Data Processing Tips**
    - Validate input coordinates before making API calls to avoid errors
    - Round coordinates to 4-6 decimal places for optimal API performance
    - Handle edge cases: coordinates in oceans may return empty results
    - Consider coordinate precision: higher precision may not yield better results
    - Implement fallback strategies for coordinates with no location data
    - Cache reverse geocoding results to improve performance for repeated queries
    - Use appropriate limits based on use case (1 for single location, 5+ for area search)

    **Common Use Cases**
    - Mobile apps: Convert GPS coordinates to readable addresses
    - Photo tagging: Add location names to geotagged images
    - Delivery services: Convert drop-off coordinates to addresses
    - IoT devices: Translate sensor locations to human-readable names
    - Emergency response: Quickly identify locations from coordinates
    - Mapping applications: Display location names for map pins
    - Fleet management: Convert vehicle positions to understandable locations
    - Social media: Tag posts with location names from GPS data
    """
    check_geo(lat, lon)

    params = {"lat": lat, "lon": lon}
    if limit is not None:
        params["limit"] = limit

    try:
        return await call_openweather_api(OpenWeatherEndpoint.CURRENT_WEATHER, params)
    except Exception as e:
        raise handle_error(e)
