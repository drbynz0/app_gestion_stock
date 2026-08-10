from internalOrders.models import InternalOrder, OrderItem, Payment
from rest_framework import serializers # type: ignore


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_ref', 'product_name', 'product_image', 'quantity', 'price']
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'payment_method', 'date', 'description']
        read_only_fields = ['id', 'date']
        
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif")
        return value

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'description']

class InternalOrderPaymentSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = InternalOrder
        fields = ['id', 'order_num', 'payments']

class InternalOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    payments = PaymentSerializer(many=True, required=False)

    class Meta:
        model = InternalOrder
        fields = [
            'id', 'order_num', 'client_id', 'client_name', 'type', 'date',
            'payment_method', 'total_price', 'total_paid', 'remaining_price',
            'status', 'description', 'items', 'payments', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        payments_data = validated_data.pop('payments', None)
        order = InternalOrder.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        if payments_data is not None:
            for payment_data in payments_data:
                PaymentSerializer.create(PaymentSerializer(), validated_data=payment_data)
        return order
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        payments_data = validated_data.pop('payments', None)

        # Mettre à jour les champs de l'InternalOrder
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Supprimer les anciens items liés à cette commande
            instance.items.all().delete()

            # Créer les nouveaux items
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        if payments_data is not None:
            # Supprimer les anciens paiements liés à cette commande

            # Créer les nouveaux paiements
            for payment_data in payments_data:
                PaymentSerializer.create(PaymentSerializer(), validated_data=payment_data)

        return instance