from .models import Address, OrderDetail
from .serializers import AddressSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, User, Product, CartDetail, Order
from .serializers import CartSerializer, ProductSerializer, OrderSerializer

class OrderViewSet(viewsets.ViewSet):

    def get_user(self, user_id):
        return get_object_or_404(User, id=user_id)

    def list(self, request, user_id=None):
        """List all orders for a user"""
        user = self.get_user(user_id)
        orders = user.orders.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, user_id=None):
        """Retrieve a specific order"""
        order = get_object_or_404(Order, id=pk, user_id=user_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"], url_path="create-from-cart")
    def create_from_cart(self, request, user_id=None):
        """
        Create a new order from the user's current cart with an address.
        Expects 'address_id' in request.data.
        """
        user = self.get_user(user_id)
        cart = getattr(user, 'cart', None)
        address_id = request.data.get("address_id")

        if not cart or not cart.items.exists():
            return Response({"error": "Cart is empty or missing."}, status=status.HTTP_400_BAD_REQUEST)

        if not address_id:
            return Response({"error": "Address ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        address = get_object_or_404(Address, id=address_id, user=user)

        order = Order.objects.create(user=user, address=address)

        for item in cart.items.all():
            OrderDetail.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                total_price=item.quantity * item.product.price
            )

        order.calculate_total_price()
        cart.clear_cart()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

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
