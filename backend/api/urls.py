from django.urls import path

from api.views import (
    AddToCartAPIView,
    LoginAPIView,
    PlaceOrderAPIView,
    ProductListCreateAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("auth/register", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login", LoginAPIView.as_view(), name="auth-login"),
    path("products", ProductListCreateAPIView.as_view(), name="products"),
    path("cart/add", AddToCartAPIView.as_view(), name="cart-add"),
    path("order/place", PlaceOrderAPIView.as_view(), name="order-place"),
]
