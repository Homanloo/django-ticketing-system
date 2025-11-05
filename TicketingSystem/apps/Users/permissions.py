from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """
    Permission check for customer users.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_active and
            request.user.user_type == 'customer'
        )


class IsAgent(permissions.BasePermission):
    """
    Permission check for agent users.
    Respects Django's is_staff flag.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_active and
            request.user.is_staff and
            request.user.user_type == 'agent'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission check for admin users.
    Respects Django's is_superuser flag.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_active and
            (request.user.user_type == 'admin' or request.user.is_superuser)
        )


class IsAgentOrAdmin(permissions.BasePermission):
    """
    Permission check for agent or admin users.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_active and
            request.user.is_staff and
            request.user.user_type in ['agent', 'admin'] or request.user.is_superuser
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj == request.user