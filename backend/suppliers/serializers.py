from rest_framework import serializers # type: ignore
from .models import Supplier
from products.models import Product
from products.serializers import ProductSerializer  # Ton serializer détaillé

class SupplierSerializer(serializers.ModelSerializer):
    # Lecture : retourner les détails complets des produits
    products_details = ProductSerializer(source='products', many=True, read_only=True)

    # Écriture : accepter une liste d’IDs
    products = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        write_only=True
    )

    class Meta:
        model = Supplier
        fields = [
            'id', 'ice', 'name_respo', 'name_ent', 'email',
            'phone', 'address',
            'products',         # pour POST/PUT (write_only)
            'products_details'  # pour GET (read_only)
        ]
