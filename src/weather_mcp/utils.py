import httpx
from mcp.server.fastmcp.exceptions import ToolError


def handle_error(error) -> ToolError:
    """
    Handles errors from the OpenWeather API calls and raises appropriate ToolError.

    Args:
        error (httpx.RequestError or httpx.HTTPStatusError): The error raised by the HTTP client.

    Raises:
        ToolError: Custom error with a user-friendly message.
    """
    if isinstance(error, httpx.HTTPStatusError):
        if error.response.status_code == 404:
            return ToolError("Weather data not found for the given location.")

        return ToolError("Weather service returned an error. Try again later.")

    elif isinstance(error, httpx.RequestError):
        return ToolError("Weather service is currently unreachable.")

    return ToolError("An unexpected error occurred.")


def check_geo(lat: float, lon: float):
    """
    Validates geographic coordinates.

    Args:
        lat (float): Latitude value.
        lon (float): Longitude value.

    Raises:
        ToolError: If latitude is not between -90.0 and 90.0, or longitude is not between -180.0 and 180.0.
    """
    if not -90.0 <= lat <= 90.0:
        raise ToolError(f"Latitude must be between -90.0 and 90.0, got {lat}")

    if not -180.0 <= lon <= 180.0:
        raise ToolError(f"Longitude must be between -180.0 and 180.0, got {lon}")
