from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from ordering.models import User, Address
from django.urls import reverse


class AddressAPITests(TestCase):

    def setUp(self):
        # Setup a test client
        self.client = APIClient()

        # Create a test user
        self.user = User.objects.create()

        # Sample address data
        self.address_data = {
            "address": "123 Cafe St, Cityville",
            "postal_code": "12345",
            "user": self.user.id
        }


    def test_create_address(self):
        """
        Test creating an address for a user.
        """
        url = reverse('address-list')
        data = self.address_data
        response = self.client.post(url, data, format='json')

        # Assert status and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['address'], data['address'])
        self.assertEqual(response.data['postal_code'], data['postal_code'])
        self.assertEqual(response.data['user'], self.user.id)

    def test_get_address(self):
        """
        Test retrieving addresses of a user.
        """
        # Create an address for the user
        Address.objects.create(user=self.user, address="123 Cafe St, Cityville", postal_code="12345")

        url = reverse('address-list')
        response = self.client.get(url)

        # Assert status and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one address created
        self.assertEqual(response.data[0]['address'], "123 Cafe St, Cityville")
        self.assertEqual(response.data[0]['postal_code'], "12345")

    def test_update_address(self):
        """
        Test updating an address for a user.
        """
        # Create an address for the user
        address = Address.objects.create(user=self.user, address="123 Cafe St, Cityville", postal_code="12345")

        # New data for update
        updated_data = {
            "address": "456 Bistro Ave, Townsville",
            "postal_code": "67890",
            "user": self.user.id
        }
        url = reverse('address-detail', args=[address.id])
        response = self.client.put(url, updated_data, format='json')

        # Assert that the address was updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], updated_data['address'])
        self.assertEqual(response.data['postal_code'], updated_data['postal_code'])

    def test_delete_address(self):
        """
        Test deleting an address.
        """
        # Create an address for the user
        address = Address.objects.create(user=self.user, address="123 Cafe St, Cityville", postal_code="12345")

        url = reverse('address-detail', args=[address.id])  # Assuming this is the URL for deleting an address
        response = self.client.delete(url)

        # Assert that the address was deleted
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Address.objects.filter(id=address.id).exists())  # Address should not exist anymore

    def test_address_validation(self):
        """
        Test validation when creating an address with invalid data.
        """
        url = reverse('address-list')

        # Missing address field
        invalid_data = {
            "postal_code": "12345"
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing postcode field
        invalid_data = {
            "address": "456 Bistro Ave, Townsville"
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
