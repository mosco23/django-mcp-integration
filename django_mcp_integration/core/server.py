"""MCP server initialization."""
from fastmcp import FastMCP
from .conf import config


# Create MCP server instance
mcp_server = FastMCP(
    name=config.name,
    version=config.version,
    instructions=config.instructions,
)
