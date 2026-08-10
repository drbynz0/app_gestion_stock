from django.db import models # type: ignore

class Activity(models.Model):
    description = models.CharField(max_length=255)
    icon_name = models.CharField(max_length=100)  # Nom de l'icône (ex: 'home', 'shopping_cart')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
