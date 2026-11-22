from rest_framework.permissions import BasePermission

ADMIN_ROLES = {"admin", "super_admin", "system_admin"}
EXPERT_ROLES = {"expert"}


class IsAdminOrSuperAdmin(BasePermission):
    message = "Only admin users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", None) in ADMIN_ROLES


class IsExpert(BasePermission):
    message = "Only expert users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", None) in EXPERT_ROLES


class IsExpertOrAdmin(BasePermission):
    message = "Only expert or admin users can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return role in ADMIN_ROLES | EXPERT_ROLES
