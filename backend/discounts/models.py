from django.db import models # type: ignore

class Discount(models.Model):
    title = models.CharField(max_length=255)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    validity = models.CharField(max_length=100)
    
    product_id = models.BigIntegerField()
    product_name = models.CharField(max_length=255)
    product_category = models.IntegerField()
    images = models.CharField(max_length=255, null=True, blank=True)

    normal_price = models.FloatField()
    promotion_price = models.FloatField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.product_name}"
