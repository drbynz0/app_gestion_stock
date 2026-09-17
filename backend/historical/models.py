from django.db import models # type: ignore
from users.models import Company

class Historical(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='history_entries', editable=False)
    description = models.TextField()
    icon = models.CharField(max_length=100)  # Nom d'icône en texte (ex: 'Icons.person_add')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.description
