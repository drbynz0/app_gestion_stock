from rest_framework import viewsets # type: ignore
from .models import Discount
from .serializers import DiscountSerializer
from users.tenancy import CompanyQuerysetMixin, IsCompanyUser

class DiscountViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [IsCompanyUser]
