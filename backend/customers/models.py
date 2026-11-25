from django.db import models # type: ignore
from django.core.validators import MinLengthValidator, RegexValidator # type: ignore
from django.utils.translation import gettext_lazy as _ # type: ignore
from users.models import Company

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customers', editable=False)
    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ['-id']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['name']),
        ]

    # Types de statuts possibles (si besoin)
    class CustomerType(models.TextChoices):
        INDIVIDUAL = 'IND', _('Particulier')
        COMPANY = 'COMP', _('Entreprise')

    # Champs principaux
    name = models.CharField(
        _("Nom complet"),
        max_length=100,
        help_text=_("Nom complet du client")
    )
    
    email = models.EmailField(
        _("Email"),
        max_length=100,
        unique=False,
        db_index=True,
        null=True,
        blank=True,
    )
    
    phone_number = models.CharField(
        _("Téléphone"),
        max_length=30,
        blank=True,
        default="",
    )
    
    address = models.TextField(
        _("Adresse"),
        max_length=200,
        null=True,
        blank=True,     
    )
    
    ice = models.CharField(
        _("ICE"),
        max_length=100,
        blank=True,
        null=True,
        unique=False,
    )
    
    is_company = models.BooleanField(
        _("Est une entreprise"),
        default=False
    )
    
    customer_type = models.CharField(
        _("Type de client"),
        max_length=4,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL
    )
    
    # Champs de dates
    created_at = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Dernière modification"),
        auto_now=True
    )

    # Relations (exemple si besoin)
    # preferred_payment_method = models.ForeignKey(
    #     'PaymentMethod',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )

    # Méthodes
    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def full_name(self):
        return self.name

    @property
    def formatted_phone(self):
        if not self.phone_number:
            return ""
        # Si le numéro commence déjà par +, on le conserve
        if self.phone_number.startswith('+'):
            return self.phone_number
        return self.phone_number

    def save(self, *args, **kwargs):
        if self.email and not self.email.strip():
            self.email = None
        if self.ice and not self.ice.strip():
            self.ice = None
        super().save(*args, **kwargs)

    def clean(self):
        """Validation supplémentaire"""
        from django.core.exceptions import ValidationError # type: ignore
        
        if self.is_company and not self.ice:
            raise ValidationError(
                {"ice": _("Un ICE est requis pour les entreprises")}
            )

    # Méthodes de classe
    @classmethod
    def get_default_client(cls):
        """Correspond à Client.empty() en Flutter"""
        return cls(
            name=_("Client par défaut"),
            email="default@client.com",
            phone_number="0000000000",
            address=_("Adresse non spécifiée"),
            is_company=False
        )

    # Correspondance avec le modèle Flutter
    def to_flutter_dict(self):
        return {
            "id": self.id,
            "ice": self.ice or "",
            "name": self.name,
            "email": self.email,
            "phone": self.phone_number,
            "address": self.address,
            "isCompagny": self.is_company,
            "fax": None,  # Correspond au getter fax dans le modèle Flutter
        }
