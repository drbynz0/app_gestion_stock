from django.urls import path # type: ignore
from .views import (
    InternalOrderListCreateView,
    InternalOrderDetailView,
    PaymentListCreateView,
    PaymentDetailView
)
urlpatterns = [
    path('', InternalOrderListCreateView.as_view(), name='internalorder-list-create'),
    path('<int:pk>/', InternalOrderDetailView.as_view(), name='internalorder-detail'),
    
    # Nouvelles URLs pour Payment
    path('<int:order_id>/payments/', 
         PaymentListCreateView.as_view(), 
         name='payment-list'),
    path('<int:order_id>/payments/<int:pk>/', 
         PaymentDetailView.as_view(), 
         name='payment-detail'),
]