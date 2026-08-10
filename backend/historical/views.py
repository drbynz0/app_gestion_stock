from rest_framework import viewsets # type: ignore
from .models import Historical
from .serializers import HistoricalSerializer

class HistoricalViewSet(viewsets.ModelViewSet):
    queryset = Historical.objects.all().order_by('-timestamp')
    serializer_class = HistoricalSerializer
