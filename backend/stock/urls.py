from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WarehouseViewSet, StockLocationViewSet, StockBalanceViewSet, StockMovementViewSet, InventoryViewSet

router = DefaultRouter()
router.register('warehouses', WarehouseViewSet, basename='warehouse')
router.register('locations', StockLocationViewSet, basename='stock-location')
router.register('balances', StockBalanceViewSet, basename='stock-balance')
router.register('movements', StockMovementViewSet, basename='stock-movement')
router.register('inventories', InventoryViewSet, basename='inventory')

urlpatterns = [path('', include(router.urls))]
