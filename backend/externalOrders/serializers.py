from externalOrders.models import ExternalOrder, OrderItem
from rest_framework import serializers # type: ignore


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_ref', 'product_name', 'product_image', 'quantity', 'price']

class ExternalOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, source='external_items')

    class Meta:
        model = ExternalOrder
        fields = [
            'id', 'order_num', 'supplier_id', 'supplier_name', 'date',
            'payment_method', 'total_price', 'total_paid', 'remaining_price',
            'status', 'description', 'items', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('external_items')
        order = ExternalOrder.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('external_items', None)

        # Mettre à jour les champs de l'ExternalOrder
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Supprimer les anciens items liés à cette commande
            instance.external_items.all().delete()

            # Créer les nouveaux items
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        return instance