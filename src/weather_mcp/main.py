import logging

from config.logging_config import setup_logging
from config.settings_config import get_settings
from weather_mcp.server import mcp

setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import weather_mcp.custom_routes  # noqa: F401
    import weather_mcp.tools  # noqa: F401

    mcp.run(transport=get_settings().mcp_transport.value)
    logger.info(f"Started {get_settings().mcp_project_info}")
