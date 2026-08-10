from rest_framework import viewsets # type: ignore
from .models import DeliveryNote
from .serializers import DeliveryNoteSerializer

class DeliveryNoteViewSet(viewsets.ModelViewSet):
    queryset = DeliveryNote.objects.all().order_by('-date')
    serializer_class = DeliveryNoteSerializer
