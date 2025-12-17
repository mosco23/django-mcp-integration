"""Base permission classes inspired by DRF."""
from typing import Any, Optional
from abc import ABC, abstractmethod


class BasePermission(ABC):
    """
    Base class for all permission classes.
    
    Similar to Django REST Framework's BasePermission.
    """
    
    message = "Permission denied."
    
    @abstractmethod
    async def has_permission(self, request: Any, tool: Any) -> bool:
        """
        Check if the request has permission to execute the tool.
        
        Args:
            request: Request context (can be dict with headers, user, etc.)
            tool: The tool instance being accessed
        
        Returns:
            True if permission granted, False otherwise
        """
        pass
    
    async def has_object_permission(
        self, 
        request: Any, 
        tool: Any, 
        obj: Any
    ) -> bool:
        """
        Check permission for a specific object.
        
        Args:
            request: Request context
            tool: The tool instance
            obj: The object being accessed
        
        Returns:
            True if permission granted, False otherwise
        """
        return True


class AllowAny(BasePermission):
    """Allow any access (no restrictions)."""
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        return True


class IsAuthenticated(BasePermission):
    """Require authentication."""
    
    message = "Authentication required."
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        user = request.get('user')
        return user is not None and getattr(user, 'is_authenticated', False)


class IsAdminUser(BasePermission):
    """Require admin/staff privileges."""
    
    message = "Admin privileges required."
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        user = request.get('user')
        return (
            user is not None 
            and getattr(user, 'is_authenticated', False)
            and getattr(user, 'is_staff', False)
        )


class IsSuperUser(BasePermission):
    """Require superuser privileges."""
    
    message = "Superuser privileges required."
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        user = request.get('user')
        return (
            user is not None 
            and getattr(user, 'is_authenticated', False)
            and getattr(user, 'is_superuser', False)
        )


class HasAPIKey(BasePermission):
    """
    Require valid API key (inspired by djangorestframework-api-key).
    
    Looks for API key in:
    1. Authorization header: "Api-Key YOUR_KEY"
    2. X-API-Key header
    3. api_key query parameter
    """
    
    message = "Valid API key required."
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        api_key = self._get_api_key(request)
        
        if not api_key:
            return False
        
        # Validate API key (implement your own validation logic)
        return await self._validate_api_key(api_key, request)
    
    def _get_api_key(self, request: Any) -> Optional[str]:
        """Extract API key from request."""
        headers = request.get('headers', {})
        
        # Check Authorization header
        auth_header = headers.get('authorization', '')
        if auth_header.startswith('Api-Key '):
            return auth_header[8:]
        
        # Check X-API-Key header
        if 'x-api-key' in headers:
            return headers['x-api-key']
        
        # Check query parameters
        query_params = request.get('query_params', {})
        if 'api_key' in query_params:
            return query_params['api_key']
        
        return None
    
    async def _validate_api_key(self, api_key: str, request: Any) -> bool:
        """
        Validate API key against database.
        
        Override this method to implement your own validation logic.
        """
        # Example: Check against Django model
        try:
            from django.contrib.auth.models import User
            # Implement your API key validation logic here
            # For example, check against a separate APIKey model
            return True  # Placeholder
        except Exception:
            return False


class HasSpecificAPIKey(HasAPIKey):
    """Require specific API key value."""
    
    def __init__(self, required_key: str):
        self.required_key = required_key
    
    async def _validate_api_key(self, api_key: str, request: Any) -> bool:
        """Validate against specific key."""
        return api_key == self.required_key


class IsOwner(BasePermission):
    """Check if user is the owner of the object."""
    
    message = "You must be the owner to perform this action."
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        # Allow access to check object-level permission
        return True
    
    async def has_object_permission(
        self, 
        request: Any, 
        tool: Any, 
        obj: Any
    ) -> bool:
        """Check if user owns the object."""
        user = request.get('user')
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        
        # Check various ownership patterns
        if hasattr(obj, 'owner'):
            return obj.owner == user
        if hasattr(obj, 'user'):
            return obj.user == user
        if hasattr(obj, 'created_by'):
            return obj.created_by == user
        
        return False


class CompositePermission(BasePermission):
    """Combine multiple permissions with AND logic."""
    
    def __init__(self, *permissions: BasePermission):
        self.permissions = permissions
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        """All permissions must pass."""
        for permission in self.permissions:
            if not await permission.has_permission(request, tool):
                self.message = permission.message
                return False
        return True
    
    async def has_object_permission(
        self, 
        request: Any, 
        tool: Any, 
        obj: Any
    ) -> bool:
        """All permissions must pass."""
        for permission in self.permissions:
            if not await permission.has_object_permission(request, tool, obj):
                self.message = permission.message
                return False
        return True


class AnyPermission(BasePermission):
    """Combine multiple permissions with OR logic."""
    
    def __init__(self, *permissions: BasePermission):
        self.permissions = permissions
    
    async def has_permission(self, request: Any, tool: Any) -> bool:
        """At least one permission must pass."""
        messages = []
        for permission in self.permissions:
            if await permission.has_permission(request, tool):
                return True
            messages.append(permission.message)
        
        self.message = " OR ".join(messages)
        return False