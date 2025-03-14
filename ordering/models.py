from django.db import models
import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

@receiver(post_save, sender=User)
def create_cart_for_user(sender, instance, created, **kwargs):
        """Automatically create a Cart when a User is created."""
        if created:
            Cart.objects.create(user=instance)

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.TextField()  # Single string for address
    postal_code = models.CharField(max_length=20)  # Postal code

    def __str__(self):
        return f"{self.address} - {self.postal_code}"

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    products = models.ManyToManyField(Product, blank=True)

    def add_products(self, product_list):
        """Converts JSON list to Product objects and adds them to the cart."""
        for product_data in product_list:
            product, _ = Product.objects.get_or_create(name=product_data["name"], price=product_data["price"])
            self.products.add(product)
        self.save()

    def remove_product(self, product_name):
        """Removes a product by name from the cart."""
        product = self.products.filter(name=product_name).first()
        if product:
            self.products.remove(product)
        self.save()

    def clear_cart(self):
        """Empties the cart."""
        self.products.clear()
        self.save()

    def total_price(self):
        """Calculates total price of all products."""
        return sum(product.price for product in self.products.all())

    def __str__(self):
        return f"Cart of {self.user.id} - {self.products.count()} items"