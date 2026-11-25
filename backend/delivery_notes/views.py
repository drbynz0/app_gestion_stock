from rest_framework import viewsets
from .models import DeliveryNote
from .serializers import DeliveryNoteSerializer
from users.tenancy import CompanyQuerysetMixin, IsCompanyUser
from historical.utils import log_activity


class DeliveryNoteViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = DeliveryNote.objects.all().order_by('-date')
    serializer_class = DeliveryNoteSerializer
    permission_classes = [IsCompanyUser]

    def perform_create(self, serializer):
        note = serializer.save(company=self.request.user.company)
        log_activity(
            self.request.user.company,
            f"Bon de livraison créé : #{getattr(note, 'note_number', getattr(note, 'number', note.id))}",
            "file-document-outline",
        )

    def perform_destroy(self, instance):
        ref = getattr(instance, 'number', instance.id)
        instance.delete()
        log_activity(self.request.user.company, f"Bon de livraison supprimé : #{ref}", "trash-can-outline")
