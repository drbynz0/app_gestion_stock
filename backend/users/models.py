import re
from django.contrib.auth.models import AbstractUser # type: ignore
from django.core.exceptions import ValidationError # type: ignore
from django.db import models # type: ignore
from django.conf import settings # type: ignore
from django.utils import timezone # type: ignore


def validate_username_format(value):
    """
    Validation stricte : uniquement des lettres minuscules, des chiffres, @ et _.
    Aucune majuscule ni caractère spécial autorisé. Longueur minimale : 3 caractères.
    """
    if not value or len(value) < 3:
        raise ValidationError("Le nom d'utilisateur doit comporter au moins 3 caractères.")
    if not re.match(r'^[a-z0-9@_]+$', value):
        raise ValidationError("Le nom d'utilisateur ne peut contenir que des lettres minuscules, chiffres, '@' et '_'.")


class Company(models.Model):
    """Tenant boundary. All business data belongs to exactly one company."""
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    company_username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_companies'
    )
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
        ('ADMIN', 'Administrateur'),
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_username_format],
        error_messages={'unique': "Ce nom d'utilisateur est déjà utilisé."},
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='ADMIN')
    is_primary_admin = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    token = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    
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


class VerificationCode(models.Model):
    CODE_TYPES = (
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('2FA', '2FA'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='verification_codes'
    )
    code_type = models.CharField(max_length=10, choices=CODE_TYPES)
    target = models.CharField(max_length=255)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"{self.code_type} code for {self.target} ({self.code})"
