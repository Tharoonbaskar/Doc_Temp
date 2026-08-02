from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    message = "Authentication is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdmin(BasePermission):
    message = "Admin access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsSuperUser(BasePermission):
    message = "Superuser access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)