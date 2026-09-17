from rest_framework import viewsets # type: ignore
from .models import FactureClient, FactureFournisseur
from .serializers import FactureClientSerializer, FactureFournisseurSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import IsCompanyAdmin

class FactureClientViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = FactureClient.objects.all().order_by('-date')
    serializer_class = FactureClientSerializer
    permission_classes = [IsCompanyAdmin]


class FactureFournisseurViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = FactureFournisseur.objects.all().order_by('-date')
    serializer_class = FactureFournisseurSerializer
    permission_classes = [IsCompanyAdmin]
