from django.db import models # type: ignore
from django.core.validators import MinLengthValidator, RegexValidator # type: ignore
from django.utils.translation import gettext_lazy as _ # type: ignore

class Customer(models.Model):
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
        unique=True,
        db_index=True
    )
    
    phone_number = models.CharField(
        _("Téléphone"),
        max_length=20,
    )
    
    address = models.TextField(
        _("Adresse"),
        max_length=200
    )
    
    ice = models.CharField(
        _("ICE"),
        max_length=100,
        blank=True,
        null=True,
        unique=True,
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
        return f"+212 {self.phone_number[1:]}" if self.phone_number.startswith('0') else self.phone_number

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