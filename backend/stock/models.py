from django.conf import settings
from django.db import models
from django.db.models import Q

from users.models import Company


class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='warehouses')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_warehouse_code_per_company')]

    def __str__(self):
        return f'{self.company} · {self.name}'


class StockLocation(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='locations')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['warehouse', 'code'], name='unique_location_code_per_warehouse')]

    def __str__(self):
        return f'{self.warehouse.code} · {self.name}'


class StockBalance(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='stock_balances')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='stock_balances')
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='stock_balances')
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'product', 'location'], name='unique_stock_balance')]


class StockMovement(models.Model):
    class Type(models.TextChoices):
        RECEIPT = 'RECEIPT', 'Entrée'
        ISSUE = 'ISSUE', 'Sortie'
        TRANSFER = 'TRANSFER', 'Transfert'
        ADJUSTMENT = 'ADJUSTMENT', 'Ajustement'
        INVENTORY = 'INVENTORY', 'Inventaire'

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='stock_movements')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='stock_movements')
    movement_type = models.CharField(max_length=16, choices=Type.choices)
    quantity = models.PositiveIntegerField()
    from_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='outgoing_movements', null=True, blank=True)
    to_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='incoming_movements', null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['company', '-created_at']), models.Index(fields=['company', 'product'])]
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name='stock_movement_quantity_positive')]


class InventorySession(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Brouillon'
        COUNTING = 'COUNTING', 'Comptage'
        VALIDATED = 'VALIDATED', 'Validé'

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='inventories')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='inventories')
    name = models.CharField(max_length=140)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='inventories_created')
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)


class InventoryLine(models.Model):
    inventory = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT)
    expected_quantity = models.IntegerField(default=0)
    counted_quantity = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['inventory', 'product', 'location'], name='unique_inventory_line')]
