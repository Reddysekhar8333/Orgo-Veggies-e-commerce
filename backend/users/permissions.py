from rest_framework.permissions import BasePermission

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