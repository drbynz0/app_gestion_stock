from rest_framework import generics # type: ignore
from .models import ExternalOrder
from .serializers import ExternalOrderSerializer

class ExternalOrderListCreateView(generics.ListCreateAPIView):
    queryset = ExternalOrder.objects.all().order_by('-created_at')
    serializer_class = ExternalOrderSerializer

class ExternalOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExternalOrder.objects.all()
    serializer_class = ExternalOrderSerializer