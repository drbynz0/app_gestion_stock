from django.utils import timezone
from rest_framework import viewsets # type: ignore
from .models import Historical
from .serializers import HistoricalSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import IsCompanyAdmin

class HistoricalViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Historical.objects.filter(is_archived=False).order_by('-timestamp')
    serializer_class = HistoricalSerializer
    permission_classes = [IsCompanyAdmin]

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.archived_at = timezone.now()
        instance.save(update_fields=['is_archived', 'archived_at'])
