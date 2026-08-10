from rest_framework.routers import DefaultRouter # type: ignore
from django.urls import path, include # type: ignore
from .views import SupplierViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
