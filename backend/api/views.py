from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers import (
    CartAddSerializer,
    LoginSerializer,
    ProductSerializer,
    RegisterSerializer,
    place_order_for_user,
)
from cart.models import CartItem
from products.models import Product
from users.permissions import IsBuyer, IsSeller


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "User registered successfully.", "username": user.username},
            status=status.HTTP_201_CREATED,
        )

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": getattr(user.profile, "role", None),
            },
            status=status.HTTP_200_OK,
        )

class ProductListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSeller()]
        return super().get_permissions()

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AddToCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        cart_item, created = CartItem.objects.get_or_create(
            buyer=request.user,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                return Response(
                    {"quantity": "Insufficient stock for updated cart quantity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity", "updated_at"])

        return Response(
            {
                "message": "Item added to cart.",
                "product_id": product.id,
                "quantity": cart_item.quantity,
            },
            status=status.HTTP_200_OK,
        )

class PlaceOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    @transaction.atomic
    def post(self, request):
        order = place_order_for_user(request.user)
        return Response(
            {
                "message": "Order placed successfully.",
                "order_id": order.id,
                "total_amount": str(order.total_amount),
            },
            status=status.HTTP_201_CREATED,
        )