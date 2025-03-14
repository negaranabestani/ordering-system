import logging

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from ordering.models import User, Cart, Product
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

        # Assert status and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(len(response.data['products']), 0)  # Cart should be empty initially

    def test_add_products_to_cart(self):
        """
        Test adding products to the cart.
        """
        url = reverse('cart-add-products', args=[self.user.id])
        data = self.products_data
        response = self.client.post(url, data, format='json')
        # Assert that the status is 200 OK and products are added to the cart
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['products']), len(self.products_data))

    def test_remove_product_from_cart(self):
        """
        Test removing a product from the cart.
        """
        # First, add some products to the cart
        self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')

        # Now, remove a product
        product_to_remove = self.products_data[0]  # Remove the first product (Pizza)
        url = reverse('cart-remove-product', args=[self.user.id])
        data = {"name": product_to_remove['name']}
        response = self.client.post(url, data, format='json')

        # Assert that the product was removed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['products']), len(self.products_data) - 1)

    def test_clear_cart(self):
        """
        Test clearing all products from the cart.
        """
        # Add some products to the cart first
        self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')

        # Clear the cart
        url = reverse('cart-clear-cart', args=[self.user.id])
        response = self.client.post(url)

        # Assert that the cart is empty
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cart']['products']), 0)

    # def test_get_cart_total_price(self):
    #     """
    #     Test getting the total price of the cart.
    #     """
    #     # Add products to the cart
    #     self.client.post(reverse('cart-add-products', args=[self.user.id]), self.products_data, format='json')
    #
    #     # Get the total price
    #     url = reverse('cart-total-price', args=[self.user.id])
    #     response = self.client.get(url)
    #
    #     # Assert that the total price is correct
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     total_price = sum(product['price'] for product in self.products_data)
    #     self.assertEqual(response.data['total_price'], total_price)

