from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter # type: ignore
from .views import HistoricalViewSet

router = DefaultRouter()
router.register(r'historical', HistoricalViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
