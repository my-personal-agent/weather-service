import logging
import os

import httpx
import psutil
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from config.settings_config import get_settings
from weather_mcp.server import mcp

logger = logging.getLogger(__name__)

# Application metrics
tool_calls_counter = Counter(
    "mcp_tool_calls_total", "Total tool calls", ["tool_name", "status"]
)
tool_duration_histogram = Histogram(
    "mcp_tool_duration_seconds", "Tool execution time", ["tool_name"]
)
active_connections = Gauge("mcp_active_connections", "Number of active MCP connections")
server_info = Info("mcp_server_info", "Server information")

# System metrics
memory_usage = Gauge("mcp_memory_usage_bytes", "Memory usage in bytes")
cpu_usage = Gauge("mcp_cpu_usage_percent", "CPU usage percentage")


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    """
    Health check endpoint to verify if the service is alive.
    This endpoint does not perform any external API calls and simply returns a 200 OK response.
    """
    logger.debug("Health check endpoint called")
    return JSONResponse(status_code=200, content={"status": "alive"})


@mcp.custom_route("/readyz", methods=["GET"])
async def readyz(request: Request) -> JSONResponse:
    """
    Readiness check endpoint to verify if the service is ready to handle requests.
    This endpoint checks the OpenWeather API to ensure it is reachable.
    If the API is reachable, it returns a 200 OK response.
    If the API is not reachable, it returns a 503 Service Unavailable response.
    """
    logger.debug("Readiness check endpoint called")
    try:
        location = "Tokyo,JP"
        params = {"q": location, "appid": get_settings().openweather_api_key}

        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                get_settings().openweather_base_url, params=params
            )

            # Raise error for any HTTP response with 4xx or 5xx status
            response.raise_for_status()

        return JSONResponse(status_code=200, content={"status": "ready"})

    except httpx.HTTPStatusError:
        return JSONResponse(
            status_code=503, content={"status": "weather_api_unavailable"}
        )

    except httpx.RequestError:
        return JSONResponse(
            status_code=503, content={"status": "error_checking_weather_api"}
        )


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> PlainTextResponse:
    """
    Metrics endpoint to expose application and system metrics in Prometheus format.
    This endpoint collects metrics such as tool calls, execution time, active connections,
    memory usage, and CPU usage.
    """
    logger.debug("Metrics endpoint called")
    process = psutil.Process(os.getpid())
    memory_usage.set(process.memory_info().rss)
    cpu_usage.set(process.cpu_percent())

    return PlainTextResponse(
        generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )


# Set server info
server_info.info(
    {"version": "1.0.0", "name": "Weather MCP", "transport": "streamable-http"}
)
