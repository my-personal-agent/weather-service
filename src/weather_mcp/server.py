from mcp.server.fastmcp import FastMCP

from config.settings_config import settings

mcp = FastMCP(
    "Weather MCP", instructions="", host=settings.mcp_host, port=settings.mcp_port
)
