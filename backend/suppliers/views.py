from rest_framework import viewsets # type: ignore
from .models import Supplier
from products.models import Product
from .serializers import SupplierSerializer
from products.serializers import ProductSerializer
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import HasSupplierPermission

class SupplierViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [HasSupplierPermission]

class ProductViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasSupplierPermission]
