from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter # type: ignore
from .views import ActivityViewSet

router = DefaultRouter()
router.register(r'activites', ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]
