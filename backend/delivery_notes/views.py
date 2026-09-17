from rest_framework import viewsets # type: ignore
from .models import DeliveryNote
from .serializers import DeliveryNoteSerializer
from users.tenancy import CompanyQuerysetMixin, IsCompanyUser

class DeliveryNoteViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = DeliveryNote.objects.all().order_by('-date')
    serializer_class = DeliveryNoteSerializer
    permission_classes = [IsCompanyUser]
