from fastmcp import FastMCP
from django.conf import settings

# Configuration MCP depuis les settings Django
MCP_CONFIG = {
    "name": getattr(settings, "MCP_SERVER_NAME", "Django MCP Server"),
    "version": getattr(settings, "MCP_SERVER_VERSION", "1.0.0"),
    "instructions": getattr(settings, "MCP_SERVER_INSTRUCTIONS", None),
    "host": getattr(settings, "MCP_HOST", "localhost"),
    "port": getattr(settings, "MCP_PORT", 8000),
    "transport": "http",
}


# Création du serveur MCP principal
mcp_server = FastMCP(
    name=MCP_CONFIG["name"],
    instructions=MCP_CONFIG["instructions"],
    version=MCP_CONFIG["version"],
)
