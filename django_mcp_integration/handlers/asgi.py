"""Enhanced ASGI handler with better error handling."""
import logging
from typing import Any, Callable, Awaitable

from ..utils.logging import get_logger

logger = get_logger(__name__)


class DjangoMCPASGIHandler:
    """Unified ASGI handler for Django and MCP requests."""
    
    def __init__(self) -> None:
        from ..core.server import mcp_server
        from django.conf import settings
        
        self.mcp_server = mcp_server
        self.mcp_path = getattr(settings, "MCP_HTTP_PATH", "/mcp/")