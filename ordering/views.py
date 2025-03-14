from .models import Address
from .serializers import AddressSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, User, Product
from .serializers import CartSerializer, ProductSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_cart(self, user_id):
        """Ensure the user has a cart. Create if missing."""
        user = get_object_or_404(User, id=user_id)
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def retrieve(self, request, pk=None):
        """Get a user's cart (always exists)."""
        cart = self.get_cart(pk)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def add_products(self, request, pk=None):
        """Add multiple products from JSON to the cart."""
        cart = self.get_cart(pk)
        product_list = request.data  # Expected: [{"name": "Pizza", "price": 10.99}, {...}]
        cart.add_products(product_list)
        return Response({"message": "Products added", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["POST"])
    def remove_product(self, request, pk=None):
        """Remove a product by name from the cart."""
        cart = self.get_cart(pk)
        product_name = request.data.get("name")
        cart.remove_product(product_name)
        return Response({"message": "Product removed", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["POST"])
    def clear_cart(self, request, pk=None):
        """Empty the cart."""
        cart = self.get_cart(pk)
        cart.clear_cart()
        return Response({"message": "Cart cleared", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["GET"])
    def total_price(self, request, pk=None):
        """Get total price of cart."""
        cart = self.get_cart(pk)
        return Response({"total_price": cart.total_price()})
