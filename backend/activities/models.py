from django.db import models # type: ignore
from users.models import Company

class Activity(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='activities', editable=False)
    description = models.CharField(max_length=255)
    icon_name = models.CharField(max_length=100)  # Nom de l'icône (ex: 'home', 'shopping_cart')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
