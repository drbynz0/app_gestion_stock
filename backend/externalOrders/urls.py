from django.urls import path # type: ignore
from .views import ExternalOrderListCreateView, ExternalOrderDetailView

urlpatterns = [
    path('', ExternalOrderListCreateView.as_view(), name='externalorder-list-create'),
    path('<int:pk>/', ExternalOrderDetailView.as_view(), name='externalorder-detail'),
]