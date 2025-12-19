"""MCP server initialization."""
from fastmcp import FastMCP
from .conf import config


# Create MCP server instance
mcp_app = FastMCP(
    name=config.name,
    version=config.version,
    instructions=config.instructions,
)

