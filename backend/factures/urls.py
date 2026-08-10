from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter # type: ignore
from .views import FactureClientViewSet, FactureFournisseurViewSet

router = DefaultRouter()
router.register(r'clients', FactureClientViewSet, basename='facture_client')
router.register(r'fournisseurs', FactureFournisseurViewSet, basename='facture_fournisseur')

urlpatterns = [
    path('', include(router.urls)),
]
