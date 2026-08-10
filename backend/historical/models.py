from django.db import models # type: ignore

class Historical(models.Model):
    description = models.TextField()
    icon = models.CharField(max_length=100)  # Nom d'icône en texte (ex: 'Icons.person_add')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
