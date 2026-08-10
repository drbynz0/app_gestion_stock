from rest_framework import viewsets # type: ignore
from .models import Supplier
from products.models import Product
from .serializers import SupplierSerializer
from products.serializers import ProductSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
