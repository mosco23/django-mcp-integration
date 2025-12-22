from typing import List

from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError

from ..core.registry import registry
from ..decorators.tools import ToolWrapper
from ..permissions.handlers import PermissionHandler


class ToolMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        result: List[ToolWrapper] = await call_next(context)
        tools = [
            registry.get_tool(tool.name) 
            for tool in result 
            if PermissionHandler.check_permissions(tool)
        ]        
        return tools
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Access the tool object to check its metadata
        if context.fastmcp_context:
            try:
                tool: ToolWrapper = registry.get_tool(context.message.name)
                if not PermissionHandler.check_permissions(tool):
                    raise ToolError(f"Access denied for tool: {tool.name}")
                
                if not tool.enabled:
                    raise ToolError("Tool is currently disabled")
                
            except Exception:
                pass
        
        return await call_next(context)
    
    