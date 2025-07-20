from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from ordering.models import User, Product, Address, Cart, CartDetail
from ordering.models import Order


class OrderAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create user and address
        self.user = User.objects.create()
        self.address = Address.objects.create(user=self.user, address="123 Test St", postal_code="111111")

        # Products
        self.product1 = Product.objects.create(name="Pizza", price=9.99)
        self.product2 = Product.objects.create(name="Pasta", price=12.50)

        # Add to cart
        self.cart = Cart.objects.get(user=self.user)
        CartDetail.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartDetail.objects.create(cart=self.cart, product=self.product2, quantity=1)

    def test_create_order_from_cart(self):
        url = reverse("orders-create-from-cart", args=[self.user.id])
        response = self.client.post(url, {"address_id": str(self.address.id)}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['user']), str(self.user.id))
        self.assertEqual(len(response.data['details']), 2)
        self.assertEqual(response.data['status'], 'accepted')

        # Check total price
        expected_total = 2 * float(self.product1.price) + 1 * float(self.product2.price)
        self.assertAlmostEqual(float(response.data['total_price']), expected_total, places=2)

    def test_cart_is_cleared_after_order(self):
        self.assertEqual(self.cart.items.count(), 2)
        self.client.post(reverse("orders-create-from-cart", args=[self.user.id]), {"address_id": self.address.id})
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.items.count(), 0)

    def test_order_has_correct_address(self):
        response = self.client.post(reverse("orders-create-from-cart", args=[self.user.id]), {"address_id": self.address.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["address"], self.address.id)

    def test_create_order_with_missing_address(self):
        url = reverse("orders-create-from-cart", args=[self.user.id])
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Address ID is required", response.data["error"])

    def test_create_order_with_empty_cart(self):
        # Clear cart
        self.cart.clear_cart()
        url = reverse("orders-create-from-cart", args=[self.user.id])
        response = self.client.post(url, {"address_id": self.address.id})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cart is empty", response.data["error"])

    def test_update_order_status(self):
        # Create order
        self.client.post(reverse("orders-create-from-cart", args=[self.user.id]), {"address_id": self.address.id})
        order = Order.objects.filter(user=self.user).first()

        # Update status
        url = reverse("orders-update-status", args=[self.user.id, order.id])
        response = self.client.patch(url, {"status": "accepted"}, format='json')
        self.assertEqual(response.data["order"]["status"], "accepted")

    def test_update_order_invalid_status(self):
        self.client.post(reverse("orders-create-from-cart", args=[self.user.id]), {"address_id": self.address.id})
        order = Order.objects.filter(user=self.user).first()

        url = reverse("orders-update-status", args=[self.user.id, order.id])
        response = self.client.patch(url, {"status": "flying"}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status", response.data["error"])

    def test_cancel_order(self):
        # Create order
        self.client.post(reverse("orders-create-from-cart", args=[self.user.id]), {"address_id": self.address.id})
        order = Order.objects.filter(user=self.user).first()

        # Cancel it
        url = reverse("orders-cancel-order", args=[self.user.id, order.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["order"]["status"], "cancelled")
