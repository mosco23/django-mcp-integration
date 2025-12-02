from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry global pour tous les tools MCP"""
    _instance = None
    _tools: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, tool_instance: Any) -> None:
        """Enregistre un tool instance"""
        tool_name = getattr(tool_instance, 'name', type(tool_instance).__name__)
        self._tools[tool_name] = tool_instance
        logger.debug(f"📝 Outil enregistré dans le registry: {tool_name}")
    
    def get_tools(self) -> List[Any]:
        """Retourne tous les tools enregistrés"""
        return list(self._tools.values())
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Retourne une tool spécifique"""
        return self._tools.get(name)
    
    def clear(self):
        """Vide le registry (pour les tests)"""
        self._tools.clear()
        logger.debug("🧹 Registry vidé")

# Instance globale du registry
registry = ToolRegistry()