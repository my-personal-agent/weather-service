import logging
from typing import Any

import httpx
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from config.settings_config import get_settings
from enums.openweather import OpenWeatherEndpoint

logger = logging.getLogger(__name__)


async def call_openweather_api(
    endpoint: OpenWeatherEndpoint,
    params: dict[str, Any],
    mcp_ctx: Context,
) -> dict[str, Any]:
    """
    Calls the specified OpenWeatherMap API endpoint with given query parameters.

    Args:
        endpoint (OpenWeatherEndpoint): Enum value representing the API endpoint to call
                                        (e.g., OpenWeatherEndpoint.WEATHER or FORECAST).
        params (dict): Query parameters for the API call. Do NOT include 'appid' or 'units';
                       these will be added automatically.
        mcp_ctx (Context): MCP context for logging or other purposes.

    Returns:
        dict: Parsed JSON response from the OpenWeather API.

    Raises:
        httpx.HTTPStatusError: If the API responds with a 4xx or 5xx error.
        httpx.RequestError: If the request fails due to network issues, timeouts, etc.
    """
    # Construct full URL to the specific OpenWeather endpoint
    url = (
        get_settings().openweather_geo_base_url
        if endpoint
        in [OpenWeatherEndpoint.DIRECT_GEOCODING, OpenWeatherEndpoint.REVERSE_GEOCODING]
        else get_settings().openweather_base_url
    )
    url = f"{url.rstrip('/')}/{endpoint.value}"

    # logging the call
    await mcp_ctx.info(
        f"Calling OpenWeather API with params (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id}) : {params}"
    )
    logger.info(
        f"Calling OpenWeather API with params : {params}",
        extra={
            "request_id": mcp_ctx.request_id,
            "client_id": mcp_ctx.client_id,
        },
    )

    # Copy original params to avoid mutating caller input
    user_params = params.copy()

    # Add API key and default units
    user_params["appid"] = get_settings().openweather_api_key
    user_params.setdefault("units", "metric")

    # report initial progress
    await mcp_ctx.report_progress(
        10, total=100, message="Preparing OpenWeather API request"
    )

    try:
        # report progress for API call
        await mcp_ctx.report_progress(
            30, total=100, message="Calling OpenWeather API request"
        )

        # Make async GET request to the API
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url, params=user_params)

            # report progress for API response
            await mcp_ctx.report_progress(
                80, total=100, message="OpenWeather API request completed"
            )

            # Raise error for any HTTP response with 4xx or 5xx status
            response.raise_for_status()

            # get JSON response
            data = response.json()

            # log and report progress for successful response
            await mcp_ctx.info(
                f"OpenWeather API response (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id}) : {data}"
            )
            await mcp_ctx.report_progress(
                100, total=100, message="OpenWeather API call successful"
            )
            logger.info(
                f"OpenWeather API response : {data}",
                extra={
                    "request_id": mcp_ctx.request_id,
                    "client_id": mcp_ctx.client_id,
                },
            )

            # Return parsed JSON data
            return data

    except httpx.HTTPStatusError as e:
        # Log HTTP error response
        logger.warning(
            f"OpenWeather API error: {e}",
            extra={"request_id": mcp_ctx.request_id, "client_id": mcp_ctx.client_id},
        )
        await mcp_ctx.warning(
            f"OpenWeather API error (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        if e.response.status_code == 404:
            raise ToolError("Weather data not found for the given location.")

        raise ToolError("Weather service returned an error. Try again later.")

    except httpx.RequestError as e:
        # Log network or connection error
        logger.error(
            f"OpenWeather API request error: {e}",
            extra={"request_id": mcp_ctx.request_id, "client_id": mcp_ctx.client_id},
        )
        await mcp_ctx.error(
            f"OpenWeather API request error (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )

        raise ToolError("An unexpected error occurred.")
