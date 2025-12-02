"""
Middleware Django pour l'intégration MCP
"""
from django.utils.deprecation import MiddlewareMixin

class MCPRequestMiddleware(MiddlewareMixin):
    """Middleware pour intégrer le contexte MCP dans les requêtes Django"""
    
    def process_request(self, request):
        # Ajoute des informations MCP à la requête
        request.mcp_available = True
        request.mcp_server = "django_mcp_integration"
        return None