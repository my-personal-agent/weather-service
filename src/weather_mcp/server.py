from mcp.server.fastmcp import FastMCP

from config.settings_config import get_settings

mcp = FastMCP(
    "Weather MCP",
    instructions="",
    host=get_settings().mcp_host,
    port=get_settings().mcp_port,
)
