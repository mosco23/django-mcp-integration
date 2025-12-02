from typing import Any, Callable, Optional, Dict, Type, get_type_hints
from .base import registry
import inspect
import logging

logger = logging.getLogger(__name__)

class SimpleToolWrapper:
    """
    Wrapper pour transformer une classe simple en outil MCP.
    """
    
    def __init__(self, tool_class: Type, name: str, description: str, input_schema: Dict = None):
        self.tool_class = tool_class
        self.name = name
        self.description = description
        self.input_schema = input_schema or self._build_input_schema(tool_class)
    
    def _build_input_schema(self, tool_class: Type) -> Dict[str, Any]:
        """Construit le schéma d'entrée à partir de la méthode execute"""
        try:
            execute_method = getattr(tool_class, 'execute')
            sig = inspect.signature(execute_method)
            
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                # Éviter **kwargs
                if param.kind == param.VAR_KEYWORD:
                    continue
                
                # Déterminer le type
                param_type = self._get_param_type(param)
                
                # Construire le schéma du paramètre
                param_schema = {"type": param_type}
                
                # Ajouter la description si disponible
                if param.default != param.empty:
                    param_schema["default"] = param.default
                else:
                    required.append(param_name)
                
                properties[param_name] = param_schema
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Impossible de construire le schéma pour {tool_class.__name__}: {e}")
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    def _get_param_type(self, param) -> str:
        """Détermine le type du paramètre"""
        if param.annotation != param.empty:
            type_map = {
                str: "string",
                int: "integer", 
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            return type_map.get(param.annotation, "string")
        return "string"
    
    async def execute(self, param) -> Any:
        """Exécute l'outil en créant une instance de la classe"""
        instance = self.tool_class()
        
        return await instance.execute(param)


def mcp_tool(name: str = None, description: str = None, input_schema: Dict = None):
    """
    Décorateur pour enregistrer une classe simple comme outil MCP.
    
    Usage:
        @mcp_tool("mon_outil", "Description")
        class MonOutil:
            async def execute(self, param) -> str:
                return f"Résultat: {param}"
    """
    def decorator(cls):
        # Validation de la classe
        if not hasattr(cls, 'execute'):
            raise ValueError(f"La classe {cls.__name__} doit avoir une méthode 'execute'")
        
        if not inspect.iscoroutinefunction(cls.execute):
            raise ValueError(f"La méthode 'execute' de {cls.__name__} doit être asynchrone (async def)")
        
        # Vérifier que la méthode n'a pas de **kwargs
        sig = inspect.signature(cls.execute)
        for param_name, param in sig.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                raise ValueError(
                    f"La méthode 'execute' de {cls.__name__} ne peut pas avoir **kwargs. "
                    f"Définissez explicitement les paramètres. Exemple: async def execute(self, param1: str, param2: int)"
                )
        
        # Déterminer les métadonnées
        tool_name = name or cls.__name__
        tool_description = description or cls.__doc__ or f"Outil {tool_name}"
        
        # Créer le wrapper
        wrapper = SimpleToolWrapper(
            tool_class=cls,
            name=tool_name,
            description=tool_description,
            input_schema=input_schema
        )
        
        # Enregistrer dans le registry
        registry.register(wrapper)
        
        # Marquer la classe comme enregistrée
        cls._mcp_tool_registered = True
        
        logger.info(f"🛠️  Outil enregistré: {tool_name}")
        
        return cls
    
    return decorator


def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Décorateur pour les fonctions.
    
    Usage:
        @tool(name="ma_fonction", description="Description")
        async def ma_fonction(param: str) -> str:
            return f"Résultat: {param}"
    """
    def decorator(func):
        # Vérifier que la fonction n'a pas de **kwargs
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                raise ValueError(
                    f"La fonction {func.__name__} ne peut pas avoir **kwargs. "
                    f"Définissez explicitement les paramètres."
                )
        
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool {tool_name}"
        
        # Créer une classe wrapper pour la fonction
        class FunctionToolWrapper:
            def __init__(self):
                self.name = tool_name
                self.description = tool_description
                self.input_schema = self._build_input_schema(func)
            
            def _build_input_schema(self, func: Callable) -> Dict[str, Any]:
                """Construit le schéma d'entrée à partir de la fonction"""
                sig = inspect.signature(func)
                type_hints = get_type_hints(func)
                
                properties = {}
                required = []
                
                for param_name, param in sig.parameters.items():
                    # Déterminer le type
                    param_type = type_hints.get(param_name, str)
                    type_str = self._python_type_to_json_type(param_type)
                    
                    # Construire le schéma
                    param_schema = {"type": type_str}
                    
                    if param.default != param.empty:
                        param_schema["default"] = param.default
                    else:
                        required.append(param_name)
                    
                    properties[param_name] = param_schema
                
                return {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            
            def _python_type_to_json_type(self, python_type: type) -> str:
                """Convertit un type Python en type JSON Schema"""
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number", 
                    bool: "boolean",
                    list: "array",
                    dict: "object"
                }
                return type_map.get(python_type, "string")
            
            async def execute(self, parm) -> Any:
                # Filtrer les kwargs pour ne garder que les paramètres valides
                
                if inspect.iscoroutinefunction(func):
                    return await func(parm)
                else:
                    return func(parm)
        
        # Enregistrer
        wrapper = FunctionToolWrapper()
        registry.register(wrapper)
        
        # Marquer la fonction comme enregistrée
        func._mcp_tool_registered = True
        
        return func
    return decorator


# Alias pour la rétrocompatibilité
def resource(uri: str = None, name: Optional[str] = None, description: Optional[str] = None):
    """Décorateur pour les ressources (alias de tool)"""
    return tool(name=name or f"resource_{uri}", description=description)

def prompt(name: Optional[str] = None, description: Optional[str] = None):
    """Décorateur pour les prompts (alias de tool)"""
    return tool(name=name, description=description)