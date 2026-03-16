from django.conf import settings
from django.db import models

from products.models import Product

class CartItem(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("buyer", "product")
    def __str__(self):
        return f"{self.buyer.username} - {self.product.name} ({self.quantity})"
