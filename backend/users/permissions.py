from rest_framework.permissions import BasePermission
from functools import wraps

class HasRole(BasePermission):
    required_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.role in self.required_roles)


class IsBuyer(HasRole):
    required_roles = ["buyer"]


class IsSeller(HasRole):
    required_roles = ["seller"]

class HasRolePermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not self.required_permission:
            return False
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.has_role_permission(self.required_permission))


class CanManageProducts(HasRolePermission):
    required_permission = "products:manage"


class CanEditCart(HasRolePermission):
    required_permission = "cart:edit"


class CanCreateOrders(HasRolePermission):
    required_permission = "orders:create"


def role_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapped(view, request, *args, **kwargs):
            user = request.user
            profile = getattr(user, "profile", None)
            if not user.is_authenticated or not profile or profile.role not in allowed_roles:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You do not have permission to perform this action.")
            return func(view, request, *args, **kwargs)

        return wrapped

    return decorator