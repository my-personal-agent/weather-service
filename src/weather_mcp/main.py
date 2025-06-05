import logging

from config.logging_config import setup_logging
from weather_mcp.server import mcp

setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import weather_mcp.custom_routes  # noqa: F401
    import weather_mcp.tools  # noqa: F401

    mcp.run(transport="streamable-http")
    logger.info("Started Weather MCP")
