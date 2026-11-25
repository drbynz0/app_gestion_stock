from django.urls import path
from .views import (
    InternalOrderListCreateView,
    InternalOrderDetailView,
    PaymentListCreateView,
    PaymentDetailView,
    InternalOrderInvoiceView,
    InternalOrderInvoiceSendView,
)
urlpatterns = [
    path('', InternalOrderListCreateView.as_view(), name='internalorder-list-create'),
    path('<int:pk>/', InternalOrderDetailView.as_view(), name='internalorder-detail'),

    # Payments
    path('<int:order_id>/payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('<int:order_id>/payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),

    # Facture PDF
    path('<int:pk>/invoice/', InternalOrderInvoiceView.as_view(), name='internal-order-invoice'),
    path('<int:pk>/invoice/send/', InternalOrderInvoiceSendView.as_view(), name='internal-order-invoice-send'),
]
