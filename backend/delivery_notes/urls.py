from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter # type: ignore
from .views import DeliveryNoteViewSet

router = DefaultRouter()
router.register(r'delivery-notes', DeliveryNoteViewSet, basename='deliverynote')

urlpatterns = [
    path('', include(router.urls)),
]
