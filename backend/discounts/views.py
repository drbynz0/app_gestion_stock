from rest_framework import viewsets, serializers as drf_serializers  # type: ignore
from django.db import transaction
from .models import Discount
from .serializers import DiscountSerializer
from users.tenancy import CompanyQuerysetMixin, IsCompanyUser
try:
    from products.models import Product
except ImportError:
    Product = None


def _sync_product_promo(product_id: int, company, enable: bool, promo_price=None):
    """
    Synchronise automatiquement le flag on_promo du produit.
    - enable=True  : active on_promo (+ promo_price si fourni)
    - enable=False : désactive on_promo si aucune autre promotion active n'existe pour ce produit
    """
    if Product is None:
        return
    try:
        product = Product.objects.get(pk=product_id, company=company)
        if enable:
            product.on_promo = True
            if promo_price is not None:
                product.promo_price = promo_price
            product.save(update_fields=['on_promo', 'promo_price'])
        else:
            # Vérifie s'il reste d'autres promotions actives pour ce produit
            still_active = Discount.objects.filter(
                product_id=product_id,
                company=company,
                validity='active',
            ).exists()
            if not still_active:
                product.on_promo = False
                product.save(update_fields=['on_promo'])
    except Product.DoesNotExist:
        pass


class DiscountViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [IsCompanyUser]

    @transaction.atomic
    def perform_create(self, serializer):
        """Crée la promotion et active automatiquement on_promo sur le produit."""
        instance = serializer.save(company=self.request.user.company)
        _sync_product_promo(
            product_id=instance.product_id,
            company=instance.company,
            enable=True,
            promo_price=instance.promotion_price,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        """Met à jour et re-synchronise le prix remisé sur le produit."""
        instance = serializer.save()
        _sync_product_promo(
            product_id=instance.product_id,
            company=instance.company,
            enable=True,
            promo_price=instance.promotion_price,
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        """Supprime la promotion et désactive on_promo si plus aucune promo active."""
        product_id = instance.product_id
        company = instance.company
        instance.delete()
        _sync_product_promo(
            product_id=product_id,
            company=company,
            enable=False,
        )
