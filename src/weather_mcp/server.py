from mcp.server.fastmcp import FastMCP

from config.settings import settings

mcp = FastMCP(
    "Weather", instructions="", host=settings.mcp_host, port=settings.mcp_port
)
