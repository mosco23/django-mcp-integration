"""Centralized configuration management."""
from typing import Optional, List
from dataclasses import dataclass, field
from django.conf import settings


@dataclass
class MCPConfig:
    """MCP server configuration with validation."""
    
    # Core settings
    enabled: bool = True
    name: str = "Django MCP Server"
    version: str = "1.0.0"
    instructions: Optional[str] = None
    
    # Network settings
    host: str = "localhost"
    port: int = 8000
    http_path: str = "/mcp"
    transport: str = "http"
    
    # Discovery settings
    auto_discover: bool = True
    discover_patterns: List[str] = field(default_factory=lambda: [
        "tools.py",
        "mcp_tools.py",
        "mcp/*.py"
    ])
    
    # Performance settings
    enable_cache: bool = True
    cache_ttl: int = 300
    max_workers: int = 4
    
    # Logging settings
    log_level: str = "INFO"
    log_requests: bool = True
    
    @classmethod
    def from_django_settings(cls) -> "MCPConfig":
        """Load configuration from Django settings."""
        return cls(
            enabled=getattr(settings, "MCP_ENABLED", cls.enabled),
            name=getattr(settings, "MCP_SERVER_NAME", cls.name),
            version=getattr(settings, "MCP_SERVER_VERSION", cls.version),
            instructions=getattr(settings, "MCP_SERVER_INSTRUCTIONS", cls.instructions),
            host=getattr(settings, "MCP_HOST", cls.host),
            port=getattr(settings, "MCP_PORT", cls.port),
            http_path=getattr(settings, "MCP_HTTP_PATH", cls.http_path),
            transport=getattr(settings, "MCP_TRANSPORT", cls.transport),
            auto_discover=getattr(settings, "MCP_AUTO_DISCOVER", cls.auto_discover),
            discover_patterns=getattr(settings, "MCP_DISCOVER_PATTERNS", cls.discover_patterns),
            enable_cache=getattr(settings, "MCP_ENABLE_CACHE", cls.enable_cache),
            cache_ttl=getattr(settings, "MCP_CACHE_TTL", cls.cache_ttl),
            max_workers=getattr(settings, "MCP_MAX_WORKERS", cls.max_workers),
            log_level=getattr(settings, "MCP_LOG_LEVEL", cls.log_level),
            log_requests=getattr(settings, "MCP_LOG_REQUESTS", cls.log_requests),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        from .exceptions import ServerConfigurationError
        
        if self.port < 1 or self.port > 65535:
            raise ServerConfigurationError(f"Invalid port: {self.port}")
        
        if self.transport not in ["http", "stdio", "sse"]:
            raise ServerConfigurationError(f"Invalid transport: {self.transport}")
        
        if not self.http_path.startswith("/"):
            raise ServerConfigurationError(f"HTTP path must start with '/': {self.http_path}")