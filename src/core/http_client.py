import logging

import httpx

from config.settings_config import settings
from enums.openweather import OpenWeatherEndpoint

logger = logging.getLogger(__name__)


async def call_openweather_api(endpoint: OpenWeatherEndpoint, params: dict) -> dict:
    """
    Calls the specified OpenWeatherMap API endpoint with given query parameters.

    Args:
        endpoint (OpenWeatherEndpoint): Enum value representing the API endpoint to call
                                        (e.g., OpenWeatherEndpoint.WEATHER or FORECAST).
        params (dict): Query parameters for the API call. Do NOT include 'appid' or 'units';
                       these will be added automatically.

    Returns:
        dict: Parsed JSON response from the OpenWeather API.

    Raises:
        httpx.HTTPStatusError: If the API responds with a 4xx or 5xx error.
        httpx.RequestError: If the request fails due to network issues, timeouts, etc.
    """
    # Construct full URL to the specific OpenWeather endpoint
    url = (
        settings.openweather_geo_base_url
        if endpoint
        in [OpenWeatherEndpoint.DIRECT_GEOCODING, OpenWeatherEndpoint.REVERSE_GEOCODING]
        else settings.openweather_base_url
    )
    url = f"{url.rstrip('/')}/{endpoint.value}"

    # Copy original params to avoid mutating caller input
    user_params = params.copy()

    # Add API key and default units
    user_params["appid"] = settings.openweather_api_key
    user_params.setdefault("units", "metric")

    try:
        # Log outbound request
        logger.info(f"Calling OpenWeather API [{endpoint.value}] with params: {params}")

        # Make async GET request to the API
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url, params=user_params)

            # Raise error for any HTTP response with 4xx or 5xx status
            response.raise_for_status()

            # Return parsed JSON response
            return response.json()

    except httpx.HTTPStatusError as e:
        # Log server-side or client-side HTTP error
        logger.warning(
            f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
        )
        raise

    except httpx.RequestError as e:
        # Log network or connection error
        logger.error(f"Request error contacting {url}: {e}")
        raise
