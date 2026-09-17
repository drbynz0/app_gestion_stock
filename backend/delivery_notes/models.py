from django.db import models # type: ignore
from users.models import Company

class DeliveryNote(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='delivery_notes', editable=False)
    note_number = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField()
    client_id = models.IntegerField(null=True, blank=True)
    client_name = models.CharField(max_length=255)
    client_address = models.TextField()
    prepared_by = models.CharField(max_length=255)
    comments = models.TextField(blank=True, null=True)
    order_num = models.CharField(max_length=100)

    def total_amount(self):
        return sum(item.quantity * item.unit_price for item in self.items.all())


class DeliveryItem(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, related_name='items', on_delete=models.CASCADE)
    product_code = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    unit_price = models.FloatField()

    @property
    def reference(self):
        return self.product_code
