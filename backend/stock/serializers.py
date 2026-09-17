from rest_framework import serializers

from products.models import Product
from .models import Warehouse, StockLocation, StockBalance, StockMovement, InventorySession, InventoryLine
from .services import record_movement, validate_inventory


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'address', 'is_active', 'created_at']


class StockLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLocation
        fields = ['id', 'warehouse', 'name', 'code', 'is_active']


class StockBalanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    class Meta:
        model = StockBalance
        fields = ['id', 'product', 'product_name', 'location', 'location_name', 'quantity', 'updated_at']


class ProductReferenceSerializer(serializers.ModelSerializer):
    """Référence légère, stable pour les écrans de stock."""
    class Meta:
        model = Product
        fields = ['id', 'name', 'code', 'stock']


class MovementActorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)


class StockMovementSerializer(serializers.ModelSerializer):
    product = ProductReferenceSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True)
    from_location = StockLocationSerializer(read_only=True)
    from_location_id = serializers.PrimaryKeyRelatedField(source='from_location', queryset=StockLocation.objects.all(), required=False, allow_null=True, write_only=True)
    to_location = StockLocationSerializer(read_only=True)
    to_location_id = serializers.PrimaryKeyRelatedField(source='to_location', queryset=StockLocation.objects.all(), required=False, allow_null=True, write_only=True)
    created_by = MovementActorSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'product_id', 'movement_type', 'quantity', 'from_location', 'from_location_id', 'to_location', 'to_location_id', 'reference', 'reason', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_product(self, product):
        if product.company_id != self.context['request'].user.company_id:
            raise serializers.ValidationError('Produit introuvable.')
        return product

    def create(self, validated_data):
        request = self.context['request']
        try:
            return record_movement(company=request.user.company, actor=request.user, **validated_data)
        except ValueError as exc:
            raise serializers.ValidationError({'non_field_errors': [str(exc)]}) from exc


class InventoryLineSerializer(serializers.ModelSerializer):
    product = ProductReferenceSerializer(read_only=True)
    location = StockLocationSerializer(read_only=True)
    class Meta:
        model = InventoryLine
        fields = ['id', 'product', 'location', 'expected_quantity', 'counted_quantity']
        read_only_fields = ['expected_quantity']


class InventorySerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    warehouse_id = serializers.PrimaryKeyRelatedField(source='warehouse', queryset=Warehouse.objects.all(), write_only=True)
    lines = InventoryLineSerializer(many=True, read_only=True)
    class Meta:
        model = InventorySession
        fields = ['id', 'warehouse', 'warehouse_id', 'name', 'status', 'created_at', 'validated_at', 'lines']
        read_only_fields = ['status', 'created_at', 'validated_at']


class InventoryCountSerializer(serializers.Serializer):
    counted_quantity = serializers.IntegerField(min_value=0)

    def update(self, instance, validated_data):
        if instance.inventory.status == InventorySession.Status.VALIDATED:
            raise serializers.ValidationError('Inventaire déjà validé.')
        instance.counted_quantity = validated_data['counted_quantity']
        instance.save(update_fields=['counted_quantity'])
        return instance
