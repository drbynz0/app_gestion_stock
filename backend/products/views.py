from email.quoprimime import unquote
import json
from rest_framework import generics, status # type: ignore
from rest_framework.response import Response # type: ignore
from .models import Product, Category, ProductImage
from .serializers import ProductSerializer, ProductCreateUpdateSerializer, CategorySerializer
from django.shortcuts import get_object_or_404 # type: ignore
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser # type: ignore
from django.core.files.storage import default_storage # type: ignore

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductListView(generics.ListAPIView):
    """Endpoint pour récupérer tous les produits (GET)"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(generics.RetrieveAPIView):
    """Endpoint pour récupérer un produit spécifique (GET)"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductCreateView(generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    serializer_class = ProductCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Créer le produit
            data = request.data.dict()
            
            # Gérer les images séparément
            images = request.FILES.getlist('images')
            
            # Valider les données
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            product = serializer.save()

            for image in images:
                # Sauvegarder l'image et obtenir le chemin relatif
                path = default_storage.save(f'products/{image.name}', image)
                ProductImage.objects.create(product=product, image=path)
                
            return Response(
                ProductSerializer(product).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProductUpdateView(generics.UpdateAPIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 1. Traitement des données standard
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 2. Gestion des images (si fournies)
        if 'images' in request.FILES:
            # Supprimer les anciennes images
            instance.images.all().delete()
            
            # Ajouter les nouvelles images
            for image in request.FILES.getlist('images'):
                path = default_storage.save(f'products/{image.name}', image)
                ProductImage.objects.create(product=instance, image=path)
        
        # 3. Retourner l'objet complet avec ses images
        updated_product = Product.objects.get(pk=instance.id)
        full_serializer = ProductSerializer(updated_product)
        
        return Response(full_serializer.data)

class ProductDeleteView(generics.DestroyAPIView):
    """Endpoint pour supprimer un produit (DELETE)"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductSearchView(generics.ListAPIView):
    """Endpoint pour rechercher des produits (GET)"""
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = Product.objects.all()
        name = self.request.query_params.get('name', None)
        category = self.request.query_params.get('category', None)
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category__name__icontains=category)
            
        return queryset