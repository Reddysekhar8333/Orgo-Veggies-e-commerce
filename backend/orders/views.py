from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from cart.models import CartItem
from orders.models import Order, OrderItem
from products.views import lock_products_for_checkout


@transaction.atomic
def place_order_for_user(user):
    cart_items = list(
        CartItem.objects.select_for_update()
        .select_related("product")
        .filter(buyer=user)
    )
    if not cart_items:
        raise serializers.ValidationError({"detail": "Cart is empty."})

    product_ids = [item.product_id for item in cart_items]
    locked_products = lock_products_for_checkout(product_ids)

    total = Decimal("0")
    order = Order.objects.create(buyer=user, total_amount=0)

    for item in cart_items:
        product = locked_products[item.product_id]
        if product.stock < item.quantity:
            raise serializers.ValidationError(
                {"detail": f"Insufficient stock for product '{product.name}'."}
            )

        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        total += product.price * item.quantity

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=product.price,
        )

    order.total_amount = total
    order.save(update_fields=["total_amount"])
    CartItem.objects.filter(id__in=[item.id for item in cart_items]).delete()
    return order