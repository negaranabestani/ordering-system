from decimal import Decimal

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


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def calculate_total_price(self):
        total = sum(detail.total_price for detail in self.details.all())
        self.total_price = total
        self.save()
        return total

    def __str__(self):
        return f"Order {self.id} by {self.user.id} - {self.total_price} Toman"


class OrderDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="details")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        # Ensure total_price is always calculated based on product.price * quantity
        self.total_price = Decimal(self.product.price) * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} = {self.total_price}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    def total_price(self):
        return sum(detail.total_price() for detail in self.items.all())

    def clear_cart(self):
        self.items.all().delete()

    def __str__(self):
        return f"Cart of {self.user.id} - {self.items.count()} items"

class CartDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")  # prevent duplicate product rows

    def increase(self, amount=1):
        self.quantity += amount
        self.save()

    def decrease(self, amount=1):
        self.quantity = max(0, self.quantity - amount)
        if self.quantity == 0:
            self.delete()
        else:
            self.save()

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart {self.cart.id}"
