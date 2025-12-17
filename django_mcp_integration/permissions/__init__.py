"""Permission system."""
from .base import (
    BasePermission,
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsSuperUser,
    HasAPIKey,
    HasSpecificAPIKey,
    IsOwner,
    CompositePermission,
    AnyPermission,
)
from .handlers import PermissionDenied, PermissionHandler

__all__ = [
    "BasePermission",
    "AllowAny",
    "IsAuthenticated",
    "IsAdminUser",
    "IsSuperUser",
    "HasAPIKey",
    "HasSpecificAPIKey",
    "IsOwner",
    "CompositePermission",
    "AnyPermission",
    "PermissionDenied",
    "PermissionHandler",
] 