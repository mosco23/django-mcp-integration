"""
Gestionnaire ASGI unifié pour Django et FastMCP.
"""

import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger("django_mcp_integration.asgi")


class DjangoMCPASGIHandler:
    """
    Gestionnaire ASGI unifié pour Django et FastMCP.
    """
    
    def __init__(self) -> None:
        # Import différé pour éviter les circulaires
        from ..server import mcp_server, MCP_CONFIG
        from django.conf import settings
        
        self.mcp_server = mcp_server
        self.mcp_path = getattr(settings, "MCP_HTTP_PATH", "/mcp")
        self.mcp_app = mcp_server.http_app(
            transport=MCP_CONFIG["transport"],
            path=self.mcp_path,
        )
        
        # Initialise le handler Django
        from django.core.handlers.asgi import ASGIHandler
        self.django_handler = ASGIHandler()

    async def __call__(
        self, 
        scope: dict[str, Any], 
        receive: Callable[[], Awaitable[dict[str, Any]]], 
        send: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Point d'entrée ASGI unifié.
        
        Route les requêtes vers MCP ou Django selon le chemin.
        """
        if scope["type"] != "http":
            raise ValueError(
                f"Django MCP peut uniquement gérer les connexions ASGI/HTTP, pas {scope['type']}."
            )

        # Vérifie si c'est une requête MCP
        path = scope.get("path", "")
        if path.startswith(self.mcp_path):
            # Route vers FastMCP
            await self.handle_mcp_request(scope, receive, send)
        else:
            # Route vers Django
            await self.django_handler(scope, receive, send)

    async def handle_mcp_request(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Gère les requêtes MCP via FastMCP."""
        try:
            await self.mcp_app(scope, receive, send)
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête MCP: {e}")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"text/plain")],
            })
            await send({
                "type": "http.response.body",
                "body": b"Internal Server Error",
                "more_body": False,
            })