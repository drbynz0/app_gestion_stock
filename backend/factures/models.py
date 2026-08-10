from django.db import models # type: ignore

class FactureClient(models.Model):
    ref = models.CharField(max_length=255)
    order_num = models.CharField(max_length=100)
    client_id = models.IntegerField()
    client_name = models.CharField(max_length=255)
    amount = models.FloatField()
    date = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_internal = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"FactureClient {self.id}"


class FactureFournisseur(models.Model):
    ref = models.CharField(max_length=50)
    order_num = models.CharField(max_length=100) 
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255)
    amount = models.FloatField()
    date = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_internal = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"FactureFournisseur {self.id}"
