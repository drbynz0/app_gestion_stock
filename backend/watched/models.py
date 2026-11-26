from django.db import models
from django.conf import settings


class WatchedItem(models.Model):
    ITEM_TYPES = [
        ('product', 'Produit'),
        ('customer', 'Client'),
        ('supplier', 'Fournisseur'),
        ('internal_order', 'Commande client'),
        ('external_order', 'Commande fournisseur'),
        ('inventory', 'Inventaire'),
        ('delivery_note', 'Bon de livraison'),
        ('discount', 'Promotion'),
        ('historical', 'Historique'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watched_items',
    )
    item_type = models.CharField(max_length=30, choices=ITEM_TYPES)
    item_id = models.PositiveIntegerField()
    item_label = models.CharField(max_length=255)
    item_meta = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item_type', 'item_id')
        ordering = ['-created_at']
        verbose_name = 'Élément suivi'
        verbose_name_plural = 'Éléments suivis'

    def __str__(self):
        return f"{self.user} → {self.item_type}#{self.item_id} ({self.item_label})"
