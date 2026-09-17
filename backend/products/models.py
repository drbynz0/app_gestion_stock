from django.db import models # type: ignore
from django.utils import timezone # type: ignore
from users.models import Company

class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='categories', editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='products', editable=False)
    name = models.CharField(max_length=255)
    variants = models.IntegerField(default=0)
    marque = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        related_name='products'
    )
    stock = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    on_promo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'code'], name='unique_product_code_per_company'),
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    # Legacy local field is kept temporarily for existing records. New uploads
    # are stored in Supabase and only their URL/key are persisted below.
    url = models.URLField(blank=True, null=True, max_length=1000)
    storage_path = models.CharField(blank=True, null=True, max_length=600, unique=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name} ({self.product.code})"
