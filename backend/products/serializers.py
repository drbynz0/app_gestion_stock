from rest_framework import serializers # type: ignore
from .models import Product, Category, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        
        
class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            'images': {'required': False}
        }
        read_only_fields = ('created_at', 'updated_at', 'category')
    

    def create(self, validated_data):
        # Extraire category_id
        category_id = validated_data.pop('category_id')
        
        # Créer le produit
        product = Product.objects.create(
            category_id=category_id,
            **validated_data
        )
        
        # Gérer les images si envoyées
        if 'images' in validated_data:
            for image in validated_data['images']:
                ProductImage.objects.create(product=product, image=image)
                
        return product