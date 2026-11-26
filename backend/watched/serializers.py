from rest_framework import serializers
from .models import WatchedItem


class WatchedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedItem
        fields = ['id', 'item_type', 'item_id', 'item_label', 'item_meta', 'created_at']
        read_only_fields = ['id', 'created_at']
