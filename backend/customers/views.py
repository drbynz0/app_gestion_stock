from rest_framework import generics, status
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import HasCustomerPermission
from historical.utils import log_activity


class CustomerListCreateView(CompanyQuerysetMixin, generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [HasCustomerPermission]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.company_id:
            # Assure la présence d'un client particulier par défaut pour les ventes comptoir
            if not Customer.objects.filter(company=user.company, name__icontains="Particulier").exists():
                Customer.objects.create(
                    company=user.company,
                    name="Client Particulier",
                    phone_number="",
                    email=None,
                    address="Vente au comptoir",
                    is_company=False,
                    customer_type=Customer.CustomerType.INDIVIDUAL,
                )
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        customer = serializer.save(company=self.request.user.company)
        log_activity(
            self.request.user.company,
            f"Client créé : {customer.name}",
            "account-plus-outline",
        )


class CustomerRetrieveUpdateDestroyView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [HasCustomerPermission]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        customer = serializer.save()
        log_activity(
            self.request.user.company,
            f"Client modifié : {customer.name}",
            "account-edit-outline",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        log_activity(request.user.company, f"Client supprimé : {name}", "account-remove-outline")
        return Response(status=status.HTTP_204_NO_CONTENT)
