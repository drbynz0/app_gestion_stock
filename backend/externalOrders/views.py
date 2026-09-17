from rest_framework import generics # type: ignore
from .models import ExternalOrder
from .serializers import ExternalOrderSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import HasOrderPermission

class ExternalOrderListCreateView(CompanyQuerysetMixin, generics.ListCreateAPIView):
    queryset = ExternalOrder.objects.all().order_by('-created_at')
    serializer_class = ExternalOrderSerializer
    permission_classes = [HasOrderPermission]

class ExternalOrderDetailView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ExternalOrder.objects.all()
    serializer_class = ExternalOrderSerializer
    permission_classes = [HasOrderPermission]
