"""Permission handling utilities."""
from typing import List, Any, Optional
from .base import BasePermission, AllowAny
from ..exceptions import DjangoMCPError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PermissionDenied(DjangoMCPError):
    """Exception raised when permission is denied."""
    
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(message)


class PermissionHandler:
    """Handle permission checks for tools."""
    
    @staticmethod
    async def check_permissions(
        permissions: List[BasePermission],
        request: Any,
        tool: Any,
        obj: Optional[Any] = None
    ) -> None:
        """
        Check all permissions and raise exception if any fail.
        
        Args:
            permissions: List of permission classes to check
            request: Request context
            tool: Tool instance
            obj: Optional object for object-level permissions
        
        Raises:
            PermissionDenied: If any permission check fails
        """
        if not permissions:
            # No permissions specified, allow access
            return
        
        # Check global permissions
        for permission in permissions:
            has_perm = await permission.has_permission(request, tool)
            
            if not has_perm:
                logger.warning(
                    f"Permission denied for tool '{getattr(tool, 'name', 'unknown')}': "
                    f"{permission.message}"
                )
                raise PermissionDenied(permission.message)
        
        # Check object-level permissions if object provided
        if obj is not None:
            for permission in permissions:
                has_obj_perm = await permission.has_object_permission(
                    request, tool, obj
                )
                
                if not has_obj_perm:
                    logger.warning(
                        f"Object permission denied for tool '{getattr(tool, 'name', 'unknown')}': "
                        f"{permission.message}"
                    )
                    raise PermissionDenied(permission.message)
        
        logger.debug(f"All permissions passed for tool '{getattr(tool, 'name', 'unknown')}'")
    
    @staticmethod
    def get_permission_classes(
        permission_classes: Optional[List[type]] = None
    ) -> List[BasePermission]:
        """
        Instantiate permission classes.
        
        Args:
            permission_classes: List of permission class types
        
        Returns:
            List of instantiated permission objects
        """
        if not permission_classes:
            return [AllowAny()]
        
        return [perm() if isinstance(perm, type) else perm 
                for perm in permission_classes]