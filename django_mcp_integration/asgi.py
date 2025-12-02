import logging
import django
from django.conf import settings
from .handlers.asgi import DjangoMCPASGIHandler


logger = logging.getLogger("django.request")
def get_asgi_application():
    """
    Retourne l'application ASGI unifiée Django-MCP.
    
    Usage typique dans asgi.py:
        from django_mcp_integration.asgi import get_asgi_application
        application = get_asgi_application()
    """
    from django.core.handlers.asgi import ASGIHandler
    
    django.setup(set_prefix=False)
    # Vérifie si l'intégration MCP est activée
    if getattr(settings, 'MCP_ENABLED', True):
        logger.info("🚀 Django MCP Integration ASGI activée")
        return DjangoMCPASGIHandler()
    else:
        logger.info("🔧 Django ASGI standard (MCP désactivé)")
        return ASGIHandler()


# Application ASGI par défaut
application = get_asgi_application()