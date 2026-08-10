from rest_framework import generics # type: ignore
from .models import InternalOrder, Payment
from .serializers import (
    InternalOrderSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    InternalOrderPaymentSerializer
)
from django.shortcuts import get_object_or_404
from rest_framework.response import Response


class InternalOrderListCreateView(generics.ListCreateAPIView):
    queryset = InternalOrder.objects.all().order_by('-created_at')
    serializer_class = InternalOrderSerializer

class InternalOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InternalOrder.objects.all()
    serializer_class = InternalOrderSerializer
    
class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return Payment.objects.filter(order_id=order_id).order_by('-date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(InternalOrder, pk=order_id)
        
        amount = serializer.validated_data['amount']
        order.total_paid += amount
        order.remaining_price = order.total_price - order.total_paid
        
        if order.remaining_price <= 0:
            order.status = 'completed'
        
        order.save()
        serializer.save(order=order)

class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return Payment.objects.filter(order_id=order_id)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PaymentCreateSerializer
        return super().get_serializer_class()

    def perform_update(self, serializer):
        payment = self.get_object()
        old_amount = payment.amount
        order = payment.order
        
        new_amount = serializer.validated_data['amount']
        amount_diff = new_amount - old_amount
        
        order.total_paid += amount_diff
        order.remaining_price = order.total_price - order.total_paid
        
        if order.remaining_price <= 0:
            order.status = 'completed'
        else:
            order.status = 'toPay'
        
        order.save()
        serializer.save()

    def perform_destroy(self, instance):
        order = instance.order
        amount = instance.amount
        
        order.total_paid -= amount
        order.remaining_price = order.total_price - order.total_paid
        
        if order.remaining_price > 0:
            order.status = 'toPay'
        
        order.save()
        instance.delete()
    
