from django.db import transaction
from django.utils import timezone

from .models import InventoryLine, InventorySession, StockBalance, StockMovement


def _balance(company, product, location):
    balance, _ = StockBalance.objects.select_for_update().get_or_create(
        company=company, product=product, location=location, defaults={'quantity': 0}
    )
    return balance


@transaction.atomic
def record_movement(*, company, actor, product, movement_type, quantity, from_location=None, to_location=None, reference='', reason=''):
    """Persist an immutable movement and update balances atomically."""
    if quantity <= 0:
        raise ValueError('La quantité doit être strictement positive.')
    locations = [location for location in (from_location, to_location) if location]
    if any(location.warehouse.company_id != company.id for location in locations):
        raise ValueError("L'emplacement n'appartient pas à votre entreprise.")
    if product.company_id != company.id:
        raise ValueError("Le produit n'appartient pas à votre entreprise.")

    if movement_type in (StockMovement.Type.ISSUE, StockMovement.Type.TRANSFER) and not from_location:
        raise ValueError('Un emplacement source est requis.')
    if movement_type == StockMovement.Type.RECEIPT and not to_location:
        raise ValueError('Un emplacement de destination est requis.')
    if movement_type == StockMovement.Type.TRANSFER and (not to_location or to_location == from_location):
        raise ValueError('Le transfert requiert deux emplacements différents.')

    if from_location:
        source = _balance(company, product, from_location)
        if movement_type in (StockMovement.Type.ISSUE, StockMovement.Type.TRANSFER) and source.quantity < quantity:
            raise ValueError('Stock insuffisant pour cette opération.')
        source.quantity -= quantity
        source.save(update_fields=['quantity', 'updated_at'])
    if to_location:
        destination = _balance(company, product, to_location)
        destination.quantity += quantity
        destination.save(update_fields=['quantity', 'updated_at'])

    return StockMovement.objects.create(
        company=company, created_by=actor, product=product, movement_type=movement_type,
        quantity=quantity, from_location=from_location, to_location=to_location,
        reference=reference, reason=reason,
    )


@transaction.atomic
def validate_inventory(*, inventory, actor):
    if inventory.status == InventorySession.Status.VALIDATED:
        raise ValueError('Cet inventaire est déjà validé.')
    for line in InventoryLine.objects.select_related('product', 'location').filter(inventory=inventory):
        if line.counted_quantity is None:
            continue
        difference = line.counted_quantity - line.expected_quantity
        if difference == 0:
            continue
        record_movement(
            company=inventory.company, actor=actor, product=line.product,
            movement_type=StockMovement.Type.INVENTORY, quantity=abs(difference),
            from_location=line.location if difference < 0 else None,
            to_location=line.location if difference > 0 else None,
            reference=f'INV-{inventory.id}', reason=f'Inventaire : {inventory.name}',
        )
    inventory.status = InventorySession.Status.VALIDATED
    inventory.validated_at = timezone.now()
    inventory.save(update_fields=['status', 'validated_at'])
    return inventory
