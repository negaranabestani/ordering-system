from .models import Address
from .serializers import AddressSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, User, Product, CartDetail
from .serializers import CartSerializer, ProductSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class CartViewSet(viewsets.ViewSet):

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
        """
        Add or increase multiple products in the cart.
        Expected format: [{"name": "Pizza", "price": 10.99, "quantity": 2}, {...}]
        """
        cart = self.get_cart(pk)
        products_data = request.data

        for item in products_data:
            name = item.get("name")
            price = item.get("price")
            quantity = item.get("quantity", 1)

            if not name or price is None:
                continue  # skip invalid item

            # Create or get the product
            product, _ = Product.objects.get_or_create(name=name, defaults={"price": price})

            # Add to cart (or increase quantity if exists)
            detail, created = CartDetail.objects.get_or_create(cart=cart, product=product)
            if not created:
                detail.increase(quantity)
            else:
                detail.quantity = quantity
                detail.save()

        return Response({"message": "Products added/updated", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["POST"])
    def remove_product(self, request, pk=None):
        """Remove a product from the cart by name (removes full row)."""
        cart = self.get_cart(pk)
        name = request.data.get("name")
        if not name:
            return Response({"error": "Product name required."}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(name=name).first()
        if not product:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        CartDetail.objects.filter(cart=cart, product=product).delete()

        return Response({"message": "Product removed", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["POST"])
    def clear_cart(self, request, pk=None):
        """Remove all items from the cart."""
        cart = self.get_cart(pk)
        cart.clear_cart()
        return Response({"message": "Cart cleared", "cart": CartSerializer(cart).data})

    @action(detail=True, methods=["GET"])
    def total_price(self, request, pk=None):
        """Calculate total price of items in the cart."""
        cart = self.get_cart(pk)
        return Response({"total_price": cart.total_price()})
