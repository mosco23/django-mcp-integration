"""MCP server initialization."""
from fastmcp import FastMCP
from ..conf import MCPConfig

# Load configuration
config = MCPConfig.from_django_settings()
config.validate()

# Create MCP server instance
mcp_server = FastMCP(
    name=config.name,
    version=config.version,
    instructions=config.instructions,
)

# Export configuration
MCP_CONFIG = {
    "name": config.name,
    "version": config.version,
    "host": config.host,
    "port": config.port,
    "transport": config.transport,
}