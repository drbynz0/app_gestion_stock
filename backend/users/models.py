from django.contrib.auth.models import AbstractUser # type: ignore
from django.db import models # type: ignore
from django.conf import settings # type: ignore

class User(AbstractUser):
    USER_TYPES = (
        ('SELLER', 'Vendeur'),
        ('ADMIN', 'Administrateur'),      
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='ADMIN')
    phone = models.CharField(max_length=20, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    
    @property
    def is_seller(self):
        return self.user_type == 'SELLER'
    
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'
    
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