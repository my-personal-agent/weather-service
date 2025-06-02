import logging

from server import mcp

from config.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Started Weather MCP")
    mcp.run()
