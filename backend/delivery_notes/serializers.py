from rest_framework import serializers # type: ignore
from .models import DeliveryNote, DeliveryItem

class DeliveryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryItem
        fields = ['id', 'product_code', 'description', 'quantity', 'unit_price']

class DeliveryNoteSerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True)

    class Meta:
        model = DeliveryNote
        fields = [
            'id', 'note_number', 'date', 'client_id', 'client_name',
            'client_address', 'prepared_by', 'comments', 'order_num', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        delivery_note = DeliveryNote.objects.create(**validated_data)
        for item_data in items_data:
            DeliveryItem.objects.create(delivery_note=delivery_note, **item_data)
        return delivery_note

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update delivery note fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()  # Supprimer les anciens éléments
            for item_data in items_data:
                DeliveryItem.objects.create(delivery_note=instance, **item_data)

        return instance
