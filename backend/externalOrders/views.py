from rest_framework import generics
from .models import ExternalOrder
from .serializers import ExternalOrderSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import HasOrderPermission
from historical.utils import log_activity


class ExternalOrderListCreateView(CompanyQuerysetMixin, generics.ListCreateAPIView):
    queryset = ExternalOrder.objects.all().order_by('-created_at')
    serializer_class = ExternalOrderSerializer
    permission_classes = [HasOrderPermission]

    def perform_create(self, serializer):
        order = serializer.save(company=self.request.user.company)
        log_activity(
            self.request.user.company,
            f"Commande fournisseur créée : #{getattr(order, 'order_num', order.id)}",
            "truck-delivery-outline",
        )


class ExternalOrderDetailView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ExternalOrder.objects.all()
    serializer_class = ExternalOrderSerializer
    permission_classes = [HasOrderPermission]

    def perform_destroy(self, instance):
        name = str(instance)
        instance.delete()
        log_activity(self.request.user.company, f"Commande fournisseur supprimée : {name}", "trash-can-outline")
