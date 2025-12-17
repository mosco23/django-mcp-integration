# Django MCP Integration

Intégration transparente de MCP (Model Context Protocol) dans Django via FastMCP.

## Installation

```bash
pip install django-mcp-integration

```

## Configuration Django


```python
# settings.py

INSTALLED_APPS = [
    # ...
    'django_mcp_integration',
]

# Utilisez l'application ASGI intégrée
ASGI_APPLICATION = "django_mcp_integration.asgi.application"


# Optionnel

MCP_SERVER_NAME = "Mon Serveur MCP"
MCP_HOST = "localhost"
MCP_PORT = 8000
MCP_HTTP_PATH = "/mcp"
MCP_ENABLED  = True
MCP_SERVER_INSTRUCTIONS = None

```

## Permissions personnalisées

### Créer une permission

```python
from django_mcp_integration.permissions import BasePermission

class IsResourceOwner(BasePermission):
    """Vérifie si l'utilisateur est propriétaire de la ressource."""
    
    def __init__(self, resource_field: str = "owner"):
        self.resource_field = resource_field
    
    def has_permission(self, request, tool) -> bool:
        return request.user.is_authenticated
    
    def has_object_permission(self, request, tool, obj) -> bool:
        return getattr(obj, self.resource_field, None) == request.user
```

## Utiliser dans un outil

```bash
from django_mcp_integration.decorators import mcp_tool

@mcp_tool(
    name="update_resource",
    description="Met à jour une ressource",
    permission_classes=[
        "IsAuthenticated",
        IsResourceOwner("author"), 
    ]
)
async def update_resource(request, resource_id: int, data: dict) -> dict:
    # Logique métier
    pass

```

## Utilisation

```bash
# Développement (remplace runserver)
python manage.py run_mcp_server

# Production
python manage.py run_mcp_server --noreload --workers 4

# Avec authentification MCP
python manage.py run_mcp_server --mcp-token my-secret-token

```


## Création de tools

```python
# blog/tools.py or blog/mcp_tools.py
from django_mcp_integration import mcp_tool
from dataclasses import dataclass

@dataclass
class Data:
    param1: str
    param2: str
    

@mcp_tool(
    name="search_posts",
    description="Recherche des articles"
)
class SearchPostsTool:
    async def execute(self, param: Data):
        from .models import Post
        posts = Post.objects.filter(published=True)
        return list(posts.values())

```
