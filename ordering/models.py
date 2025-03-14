from django.db import models

from django.db import models
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.TextField()  # Single string for address
    postal_code = models.CharField(max_length=20)  # Postal code

    def __str__(self):
        return f"{self.address} - {self.postal_code}"
