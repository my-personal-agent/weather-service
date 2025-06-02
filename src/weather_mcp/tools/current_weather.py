import logging

import httpx
from server import mcp

from config.settings_config import settings

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_current_weather(city: str, country_code: str | None = None) -> dict:
    """
    Fetches the current weather for a specified city using the OpenWeather API.

    Args:
        city (str): The name of the city (e.g., "Tokyo").
        country_code (str | None): Optional 2-letter country code (e.g., "JP"). If provided, the API will use "city,country_code".

    Returns:
        dict: JSON response from the OpenWeather API, including temperature,
              weather condition, humidity, etc.

    Raises:
        httpx.HTTPStatusError: Raised if the API returns a 4xx/5xx error.
        httpx.RequestError: Raised if the request fails due to connection issues.
    """
    try:
        # Build location query (e.g., "Tokyo,JP" or just "Tokyo")
        location = f"{city},{country_code}" if country_code else city

        params = {
            "q": location,
            "appid": settings.openweather_api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(settings.openweather_base_url, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(
            f"OpenWeather API returned HTTP error {e.response.status_code} "
            f"for city='{city}' country_code='{country_code}': {e.response.text}"
        )
        raise

    except httpx.RequestError as e:
        logger.error(
            f"Failed to connect to OpenWeather API for city='{city}' "
            f"country_code='{country_code}': {e}"
        )
        raise
