from django.conf import settings
from django.db import models

class UserRole(models.TextChoices):
    VISITOR = "visitor", "Visitor"
    BUYER = "buyer", "Buyer"
    SELLER = "seller", "Seller"

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VISITOR)
    ROLE_PERMISSIONS = {
        UserRole.VISITOR: frozenset({"products:view"}),
        UserRole.BUYER: frozenset({"products:view", "cart:edit", "orders:create"}),
        UserRole.SELLER: frozenset({"products:view", "products:manage"}),
    }

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    @property
    def allowed_permissions(self):
        return self.ROLE_PERMISSIONS.get(self.role, frozenset())

    def has_role_permission(self, permission_name):
        return permission_name in self.allowed_permissions
