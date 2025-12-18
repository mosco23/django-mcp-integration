"""
Enhanced ASGI application supporting multiple servers (Uvicorn, Daphne, Gunicorn, runserver).
Compatible with both django_mcp_integration.asgi:application and myproject.asgi:application
"""

import django
from django.core.handlers.asgi import ASGIHandler
from fastmcp import FastMCP

from ..core.conf import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DjangoMCPApplication:
    """
    Unified ASGI application that routes requests between Django and MCP.
    Compatible with Uvicorn, Daphne, Gunicorn, and Django's runserver.
    """
    
    def __init__(self, django_app: ASGIHandler, mcp_app: FastMCP):
        self.django_app = django_app
        self.mcp_app = mcp_app
    
    async def __call__(self, scope, receive, send):
        """
        ASGI3 application callable.
        
        Routes requests to either MCP server or Django based on path.
        Compatible with runserver and all ASGI servers.
        """
        if scope["type"] == "lifespan":
            # Handle lifespan events (for Uvicorn, Daphne, etc.)
            await self._handle_lifespan(scope, receive, send)
            return
        
        # Get request path
        path = scope.get("path", "")
        
        from ..core.conf import config
        
        # Route to MCP if enabled and path matches
        if config.enabled and path.startswith(config.http_path):
            logger.debug(f"📡 Routing to MCP: {path}")
            try:
                # FastMCP server implements __call__ directly
                await self.mcp_app(scope, receive, send)
            except Exception as e:
                logger.error(f"❌ MCP error: {e}", exc_info=True)
                # Fallback to Django for error handling
                await self.django_app(scope, receive, send)
        else:
            # Route to Django
            logger.debug(f"🌐 Routing to Django: {path}")
            await self.django_app(scope, receive, send)
    
    async def _handle_lifespan(self, scope, receive, send):
        """Handle ASGI lifespan protocol."""
        while True:
            message = await receive()
            
            if message["type"] == "lifespan.startup":
                try:
                    logger.info("🟢 Application startup")
                    await send({"type": "lifespan.startup.complete"})
                except Exception as e:
                    logger.error(f"❌ Startup failed: {e}")
                    await send({
                        "type": "lifespan.startup.failed",
                        "message": str(e)
                    })
            
            elif message["type"] == "lifespan.shutdown":
                try:
                    logger.info("🔴 Application shutdown")
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as e:
                    logger.error(f"❌ Shutdown failed: {e}")
                    await send({
                        "type": "lifespan.shutdown.failed",
                        "message": str(e)
                    })
                return



def get_mcp_asgi_application():
    """
    Helper function to get the ASGI application.
    Can be used in custom ASGI files.
    """
    django.setup(set_prefix=False)
    return  DjangoMCPApplication()