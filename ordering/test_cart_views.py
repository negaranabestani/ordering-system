import logging
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from ordering.models import User, Cart, Product, CartDetail
from django.urls import reverse


class CartAPITests(TestCase):

    def setUp(self):
        # Setup a test client
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create()

        # Create a cart for the user
        # self.cart = Cart.objects.create(user=self.user)

        # Sample product data
        self.products_data = [
            {"name": "Pizza", "price": 9.99},
            {"name": "Pasta", "price": 12.50},
        ]


    def test_get_user_cart(self):
        """
        Test retrieving the cart for a user.
        """
        url = reverse('cart-detail', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['user']), str(self.user.id))
        self.assertEqual(len(response.data['items']), 0)


    def test_add_products_to_cart(self):
        """
        Test adding products to the cart with quantities.
        """
        url = reverse('cart-add-products', args=[self.user.id])
        response = self.client.post(url, self.products_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['items']), len(self.products_data))

        # Optional: check quantity matches
        item_map = {item['product']['name']: item['quantity'] for item in response.data['cart']['items']}
        for product in self.products_data:
            self.assertEqual(item_map[product['name']], 1)

    def test_remove_product_from_cart(self):
        """
        Test removing a product from the cart.
        """
        # Add products first
        self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')

        product_to_remove = self.products_data[0]  # "Pizza"
        url = reverse('cart-remove-product', args=[self.user.id])
        response = self.client.post(url, {"name": product_to_remove['name']}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item_names = [item['product']['name'] for item in response.data['cart']['items']]
        self.assertNotIn(product_to_remove['name'], item_names)
        self.assertEqual(len(response.data['cart']['items']), 1)

    def test_clear_cart(self):
        """
        Test clearing all products from the cart.
        """
        self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')

        url = reverse('cart-clear-cart', args=[self.user.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['items']), 0)
        self.assertEqual(CartDetail.objects.filter(cart__user=self.user).count(), 0)

    def test_get_cart_total_price(self):
        """
        Test getting the total price of the cart.
        """
        self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')

        url = reverse('cart-total-price', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Compute expected total price based on quantity
        expected_total = sum(Decimal(p['price']* 1) for p in self.products_data)
        self.assertAlmostEqual(response.data['total_price'], expected_total, places=2)