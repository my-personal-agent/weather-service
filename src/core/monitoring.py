# Application metrics
from prometheus_client import Counter, Gauge, Histogram, Info

from config.settings_config import get_settings

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

# Set server info
server_info.info(
    {
        "version": get_settings().mcp_project_version,
        "name": get_settings().mcp_project_name,
        "transport": get_settings().mcp_transport.value,
    }
)
