"""Django MCP Integration - Professional version."""
from .decorators import mcp_tool, tool, resource, prompt
from .core.registry import registry
from .exceptions import (
    DjangoMCPError,
    ToolRegistrationError,
    InvalidToolSignatureError,
    ToolDiscoveryError,
    ServerConfigurationError,
)

__version__ = "1.0.0"
__all__ = [
    "mcp_tool",
    "tool",
    "resource",
    "prompt",
    "registry",
    "DjangoMCPError",
    "ToolRegistrationError",
    "InvalidToolSignatureError",
    "ToolDiscoveryError",
    "ServerConfigurationError",
]