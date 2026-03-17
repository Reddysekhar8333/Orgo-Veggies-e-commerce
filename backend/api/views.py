from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers import (
    CartAddSerializer,
    CartItemSerializer,
    CartRemoveSerializer,
    LoginSerializer,
    ProductSerializer,
    RegisterSerializer,
)
from cart.models import CartItem
from orders.views import place_order_for_user
from products.models import Product
from users.permissions import (
    CanCreateOrders,
    CanEditCart,
    CanManageProducts,
    IsBuyer,
    IsSeller,
    role_required,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFCookieAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)}, status=status.HTTP_200_OK)

@method_decorator(csrf_protect, name="dispatch")
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
    
@method_decorator(csrf_protect, name="dispatch")
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
                "token_type": "Bearer",
            },
            status=status.HTTP_200_OK,
        )

class ProductListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSeller(), CanManageProducts()]
        return super().get_permissions()

    def get(self, request):
        products = Product.objects.all()
        query = request.query_params.get("q")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        in_stock = request.query_params.get("in_stock")
        if query:
            products = products.filter(name__icontains=query)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if in_stock == "true":
            products = products.filter(stock__gt=0)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @method_decorator(role_required("seller"))
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, _request, product_id):
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ProductStockValidationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id):
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.query_params.get("quantity", 1))
        return Response(
            {
                "product_id": product.id,
                "requested_quantity": quantity,
                "available_stock": product.stock,
                "is_available": quantity <= product.stock,
            },
            status=status.HTTP_200_OK,
        )



@method_decorator(csrf_protect, name="dispatch")
class AddToCartAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsBuyer, CanEditCart]

    @method_decorator(role_required("buyer"))
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

@method_decorator(csrf_protect, name="dispatch")
class PlaceOrderAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsBuyer, CanCreateOrders]

    @method_decorator(role_required("buyer"))
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

class CartAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsBuyer, CanEditCart]

    def get(self, request):
        cart_items = CartItem.objects.filter(buyer=request.user).select_related("product")
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)


@method_decorator(csrf_protect, name="dispatch")
class RemoveCartItemAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsBuyer, CanEditCart]

    @method_decorator(role_required("buyer"))
    def post(self, request):
        serializer = CartRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]

        deleted, _ = CartItem.objects.filter(buyer=request.user, product_id=product_id).delete()
        if not deleted:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"message": "Item removed from cart.", "product_id": product_id})

