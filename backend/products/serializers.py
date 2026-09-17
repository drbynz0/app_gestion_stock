from rest_framework import serializers # type: ignore
from .models import Product, Category, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at')

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

    def get_image(self, obj):
        """Return the Supabase URL; fall back to legacy Django media records."""
        if obj.url:
            return obj.url
        return obj.image.url if obj.image else None

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'variants', 'marque', 'code', 'category', 'stock',
            'available', 'price', 'promo_price', 'description', 'on_promo',
            'images', 'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')
        
        
class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=True
    )

    class Meta:
        model = Product
        fields = [
            'name', 'variants', 'marque', 'code', 'category_id', 'stock',
            'available', 'price', 'promo_price', 'description', 'on_promo',
        ]
        read_only_fields = ('category',)

    def validate_category(self, category):
        request = self.context['request']
        company = getattr(request.user, 'company', None)
        if not company or category.company_id != company.id:
            raise serializers.ValidationError("Catégorie introuvable dans votre entreprise.")
        return category
    

    def create(self, validated_data):
        # Extraire category_id
        category = validated_data.pop('category')
        
        # Créer le produit
        product = Product.objects.create(
            category=category,
            **validated_data
        )
        
        # Gérer les images si envoyées
        if 'images' in validated_data:
            for image in validated_data['images']:
                ProductImage.objects.create(product=product, image=image)
                
        return product
