from rest_framework import serializers # type: ignore
from .models import FactureClient, FactureFournisseur

class FactureClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactureClient
        fields = ['id', 'ref', 'order_num', 'client_id', 'client_name', 'amount', 'date', 'description', 'is_internal', 'is_paid']


class FactureFournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactureFournisseur
        fields = ['id', 'ref', 'order_num', 'supplier_id', 'supplier_name', 'amount', 'date', 'description', 'is_internal', 'is_paid']
