from rest_framework import viewsets # type: ignore
from .models import FactureClient, FactureFournisseur
from .serializers import FactureClientSerializer, FactureFournisseurSerializer

class FactureClientViewSet(viewsets.ModelViewSet):
    queryset = FactureClient.objects.all().order_by('-date')
    serializer_class = FactureClientSerializer


class FactureFournisseurViewSet(viewsets.ModelViewSet):
    queryset = FactureFournisseur.objects.all().order_by('-date')
    serializer_class = FactureFournisseurSerializer
