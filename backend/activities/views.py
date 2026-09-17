from rest_framework import viewsets # type: ignore
from .models import Activity
from .serializers import ActivitySerializer
from users.tenancy import CompanyQuerysetMixin, IsCompanyUser

class ActivityViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Activity.objects.all().order_by('-timestamp')
    serializer_class = ActivitySerializer
    permission_classes = [IsCompanyUser]
