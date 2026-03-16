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

    def __str__(self):
        return f"{self.user.username} ({self.role})"
