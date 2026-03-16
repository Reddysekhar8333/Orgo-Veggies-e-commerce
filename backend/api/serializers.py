from django.core.validators import validate_email
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from products.models import Product
from users.models import UserRole


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    role = serializers.ChoiceField(choices=[UserRole.BUYER, UserRole.SELLER], write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def validate_username(self, value):
        cleaned = strip_tags(value).strip()
        if not cleaned:
            raise serializers.ValidationError("Username cannot be empty.")
        return cleaned

    def validate_email(self, value):
        cleaned = strip_tags(value).strip().lower()
        validate_email(cleaned)
        return cleaned

    def create(self, validated_data):
        role = validated_data.pop("role")
        user = User.objects.create_user(**validated_data)
        user.profile.role = role
        user.profile.save(update_fields=["role"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = strip_tags(attrs["username"]).strip()
        password = attrs["password"]
        user = authenticate(username=username, password=password)
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
    def validate_name(self, value):
        cleaned = strip_tags(value).strip()
        if not cleaned:
            raise serializers.ValidationError("Product name cannot be empty.")
        return cleaned

    def validate_description(self, value):
        return strip_tags(value).strip()


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

