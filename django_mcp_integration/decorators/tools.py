"""Unified tool decorator supporting both classes and functions."""
import inspect
from typing import Any, Callable, Dict, Optional, Type, Union, List
from ..core.registry import registry
from ..exceptions import InvalidToolSignatureError
from ..permissions.base import BasePermission
from ..permissions.handlers import PermissionHandler
from ..utils.logging import get_logger, log_tool_execution

logger = get_logger(__name__)


class ToolWrapper:
    """Unified wrapper for both class-based and function-based tools."""
    
    def __init__(
        self,
        target: Union[Type, Callable],
        name: str,
        description: str,
        permission_classes: Optional[List[Type[BasePermission]]] = None,
        input_schema: Optional[Dict] = None
    ):
        self.target = target
        self.name = name
        self.description = description
        self.permission_classes = PermissionHandler.get_permission_classes(
            permission_classes
        )
        self.is_class = inspect.isclass(target)
        self.input_schema = input_schema or self._build_input_schema()
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate tool structure."""
        if self.is_class:
            self._validate_class()
        else:
            self._validate_function()
    
    def _validate_class(self) -> None:
        """Validate class-based tool."""
        if not hasattr(self.target, 'execute'):
            raise InvalidToolSignatureError(
                self.target.__name__,
                "Tool class must have an 'execute' method"
            )
        
        if not inspect.iscoroutinefunction(self.target.execute):
            raise InvalidToolSignatureError(
                self.target.__name__,
                "'execute' method must be async (async def)"
            )
        
        self._check_kwargs(self.target.execute, self.target.__name__)
    
    def _validate_function(self) -> None:
        """Validate function-based tool."""
        if not inspect.iscoroutinefunction(self.target):
            raise InvalidToolSignatureError(
                self.target.__name__,
                "Tool function must be async (async def)"
            )
        
        self._check_kwargs(self.target, self.target.__name__)
    
    def _check_kwargs(self, func: Callable, name: str) -> None:
        """Check for **kwargs in signature."""
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                raise InvalidToolSignatureError(
                    name,
                    f"Tool cannot use **kwargs. Define parameters explicitly."
                )
    
    def _build_input_schema(self) -> Dict[str, Any]:
        """Build JSON schema from signature."""
        try:
            if self.is_class:
                func = self.target.execute
            else:
                func = self.target
            
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self' or param_name == 'request':
                    continue
                
                if param.kind == param.VAR_KEYWORD:
                    continue
                
                param_type = self._get_param_type(param)
                param_schema = {"type": param_type}
                
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
            logger.warning(f"⚠️  Could not build schema: {e}")
            return {"type": "object", "properties": {}, "required": []}
    
    def _get_param_type(self, param) -> str:
        """Determine JSON type from parameter annotation."""
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
    
    @log_tool_execution
    async def execute(self, request: Any = None, **kwargs) -> Any:
        """
        Execute the tool with permission checks.
        
        Args:
            request: Request context (for permissions)
            **kwargs: Tool parameters
        """
        # Create request context if not provided
        if request is None:
            request = {}
        
        # Check permissions
        await PermissionHandler.check_permissions(
            self.permission_classes,
            request,
            self
        )
        
        # Execute the tool
        if self.is_class:
            instance = self.target()
            return await instance.execute(**kwargs)
        else:
            return await self.target(**kwargs)


def mcp_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    input_schema: Optional[Dict] = None
):
    """
    Unified decorator for both class and function-based tools.
    
    Args:
        name: Tool name (defaults to class/function name)
        description: Tool description (defaults to docstring)
        permission_classes: List of permission classes (DRF-style)
        input_schema: JSON schema for input validation
    
    Examples:
        # Class-based tool
        @mcp_tool(
            name="create_post",
            description="Create a blog post",
            permission_classes=[IsAuthenticated, HasAPIKey]
        )
        class CreatePostTool:
            async def execute(self, title: str, content: str):
                # Implementation
                pass
        
        # Function-based tool
        @mcp_tool(
            name="get_posts",
            permission_classes=[AllowAny]
        )
        async def get_posts(limit: int = 10):
            # Implementation
            pass
    """
    def decorator(target: Union[Type, Callable]) -> Union[Type, Callable]:
        # Determine if it's a class or function
        is_class = inspect.isclass(target)
        
        # Determine metadata
        tool_name = name or target.__name__
        tool_description = description or target.__doc__ or f"Tool {tool_name}"
        
        # Create wrapper
        wrapper = ToolWrapper(
            target=target,
            name=tool_name,
            description=tool_description,
            permission_classes=permission_classes,
            input_schema=input_schema
        )
        
        # Register in registry
        registry.register(wrapper, metadata={
            "type": "class" if is_class else "function",
            "permissions": [p.__class__.__name__ for p in wrapper.permission_classes]
        })
        
        # Mark as registered
        target._mcp_tool_registered = True
        
        logger.info(
            f"🛠️  {'Class' if is_class else 'Function'} tool registered: {tool_name}"
        )
        
        return target
    
    return decorator


# Aliases for convenience
tool = mcp_tool
resource = mcp_tool
prompt = mcp_tool