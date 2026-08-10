from django.db import models # type: ignore
from products.models import Product


class Supplier(models.Model):
    ice = models.CharField(max_length=15, unique=True)  # Identifiant unique
    name_respo = models.CharField(max_length=100)
    name_ent = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.name_ent
