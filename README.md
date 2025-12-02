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
