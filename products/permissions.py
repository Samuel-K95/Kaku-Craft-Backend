from rest_framework.permissions import BasePermission


class IsAdminOrSuperAdmin(BasePermission):
    message = "Only admin users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", None) in {"admin", "super_admin"}
