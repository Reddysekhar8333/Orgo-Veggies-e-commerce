from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from cart.models import CartItem
from orders.models import Order, OrderItem
from products.models import Product
from users.models import UserRole


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[UserRole.BUYER, UserRole.SELLER], write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role")
        user = User.objects.create_user(**validated_data)
        user.profile.role = role
        user.profile.save(update_fields=["role"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid username or password."})
        attrs["user"] = user
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source="seller.username", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "stock", "seller", "created_at"]
        read_only_fields = ["id", "seller", "created_at"]


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist.")
        return value

    def validate(self, attrs):
        product = Product.objects.get(id=attrs["product_id"])
        if product.stock < attrs["quantity"]:
            raise serializers.ValidationError({"quantity": "Insufficient stock available."})
        attrs["product"] = product
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "total_amount", "created_at"]


def place_order_for_user(user):
    cart_items = CartItem.objects.select_related("product").filter(buyer=user)
    if not cart_items.exists():
        raise serializers.ValidationError({"detail": "Cart is empty."})

    total = Decimal("0")
    order = Order.objects.create(buyer=user, total_amount=0)

    for item in cart_items:
        product = item.product
        if product.stock < item.quantity:
            order.delete()
            raise serializers.ValidationError(
                {"detail": f"Insufficient stock for product '{product.name}'."}
            )
        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        line_total = product.price * item.quantity
        total += line_total
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=product.price,
        )

    order.total_amount = total
    order.save(update_fields=["total_amount"])
    cart_items.delete()
    return order
