from django.contrib.auth.models import AbstractUser # type: ignore
from django.db import models # type: ignore
from django.conf import settings # type: ignore


class Company(models.Model):
    """Tenant boundary. All business data belongs to exactly one company."""
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default='MAD')
    logo_uri = models.TextField(blank=True, default='')
    primary_color = models.CharField(max_length=9, default='#00E599')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    USER_TYPES = (
        ('SELLER', 'Vendeur'),
        ('ADMIN', 'Administrateur entreprise'),
        ('PLATFORM_ADMIN', 'Administrateur plateforme'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='ADMIN')
    phone = models.CharField(max_length=20, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    
    @property
    def is_seller(self):
        return self.user_type == 'SELLER'
    
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'

    @property
    def is_platform_admin(self):
        return self.user_type == 'PLATFORM_ADMIN' or self.is_superuser
    
    @property
    def seller_privileges(self):
        if self.is_seller:
            return getattr(self, 'privileges', None)
        return None
    
class SellerPrivileges(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='privileges')
    add_product = models.BooleanField(default=False)
    edit_product = models.BooleanField(default=False)
    delete_product = models.BooleanField(default=False)
    add_order = models.BooleanField(default=False)
    edit_order = models.BooleanField(default=False)
    delete_order = models.BooleanField(default=False)
    add_client = models.BooleanField(default=False)
    edit_client = models.BooleanField(default=False)
    delete_client = models.BooleanField(default=False)
    add_supplier = models.BooleanField(default=False)
    edit_supplier = models.BooleanField(default=False)
    delete_supplier = models.BooleanField(default=False)
    add_category = models.BooleanField(default=False)
    edit_category = models.BooleanField(default=False)
    delete_category = models.BooleanField(default=False)

    def __str__(self):
        return f"Privileges for {self.user.username}"
