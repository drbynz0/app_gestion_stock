from django.db import transaction
from django.db.models import Q
from django.db.transaction import on_commit
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import APIException, ValidationError

from .models import Product, Category, ProductImage
from .permissions import HasCategoryPermission, HasProductPermission
from .serializers import ProductSerializer, ProductCreateUpdateSerializer, CategorySerializer
from .storage import delete_product_image, upload_product_image
from historical.utils import log_activity

MAX_PRODUCT_IMAGES = 4


class CompanyQuerysetMixin:
    """Ensures an object can only ever be read inside the caller's company."""
    def get_queryset(self):
        if self.request.user.user_type == 'PLATFORM_ADMIN' or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(company=self.request.user.company)


class CategoryListView(CompanyQuerysetMixin, generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [HasCategoryPermission]

    def perform_create(self, serializer):
        category = serializer.save(company=self.request.user.company)
        log_activity(self.request.user.company, f"Catégorie créée : {category.name}", "shape-outline")


class CategoryDetailView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [HasCategoryPermission]

    def perform_update(self, serializer):
        category = serializer.save()
        log_activity(self.request.user.company, f"Catégorie modifiée : {category.name}", "pencil-outline")

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        log_activity(self.request.user.company, f"Catégorie supprimée : {name}", "trash-can-outline")


# Compatibility endpoint retained for the existing mobile client.
CategoryCreateView = CategoryListView
CategoryUpdateView = CategoryDetailView
CategoryDeleteView = CategoryDetailView


class ProductListView(CompanyQuerysetMixin, generics.ListAPIView):
    queryset = Product.objects.select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [HasProductPermission]


class ProductDetailView(CompanyQuerysetMixin, generics.RetrieveAPIView):
    queryset = Product.objects.select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [HasProductPermission]


class ProductCreateView(generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [HasProductPermission]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist('images')
        if len(images) > MAX_PRODUCT_IMAGES:
            raise ValidationError({'images': [f"Maximum {MAX_PRODUCT_IMAGES} images autorisées par produit."]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(company=request.user.company)
        self._store_images(request, product)
        log_activity(request.user.company, f"Produit créé : {product.name} (réf. {product.code})", "plus-circle-outline")
        return Response(ProductSerializer(product, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _store_images(request, product):
        has_main = product.images.filter(is_main=True).exists()
        for index, image in enumerate(request.FILES.getlist('images')):
            try:
                url, storage_path = upload_product_image(
                    file=image, company_id=product.company_id, product_id=product.id
                )
            except ValueError as exc:
                raise ValidationError({'images': [str(exc)]}) from exc
            except RuntimeError as exc:
                error = APIException("Le stockage des images est temporairement indisponible.")
                error.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                raise error from exc
            is_main = (not has_main and index == 0)
            ProductImage.objects.create(product=product, url=url, storage_path=storage_path, is_main=is_main)


class ProductUpdateView(CompanyQuerysetMixin, generics.UpdateAPIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [HasProductPermission]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 1. Suppression des images spécifiées si demandé
        raw_remove = request.data.get('removed_image_ids')
        if raw_remove:
            if isinstance(raw_remove, str):
                import json
                try:
                    remove_ids = json.loads(raw_remove)
                except Exception:
                    remove_ids = [int(i.strip()) for i in raw_remove.split(',') if i.strip().isdigit()]
            elif isinstance(raw_remove, (list, tuple)):
                remove_ids = raw_remove
            else:
                remove_ids = []

            if remove_ids:
                to_delete = product.images.filter(id__in=remove_ids)
                stale_paths = list(to_delete.exclude(storage_path__isnull=True).values_list('storage_path', flat=True))
                to_delete.delete()
                if stale_paths:
                    on_commit(lambda: [delete_product_image(path) for path in stale_paths])

        # 2. Ajout cumulatif des nouvelles images sans remplacer les anciennes
        new_images = request.FILES.getlist('images')
        if new_images:
            existing_count = product.images.count()
            if existing_count + len(new_images) > MAX_PRODUCT_IMAGES:
                raise ValidationError({
                    'images': [f"Le produit contient déjà {existing_count} image(s). Maximum {MAX_PRODUCT_IMAGES} images au total."]
                })
            ProductCreateView._store_images(request, product)

        # 3. Assurer qu'au moins une image est principale s'il reste des images
        if product.images.exists() and not product.images.filter(is_main=True).exists():
            first_img = product.images.first()
            first_img.is_main = True
            first_img.save(update_fields=['is_main'])

        log_activity(request.user.company, f"Produit modifié : {product.name}", "pencil-outline")
        return Response(ProductSerializer(product, context=self.get_serializer_context()).data)


class ProductDeleteView(CompanyQuerysetMixin, generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasProductPermission]

    def perform_destroy(self, instance):
        name = instance.name
        stale_paths = list(instance.images.exclude(storage_path__isnull=True).values_list('storage_path', flat=True))
        instance.delete()
        log_activity(self.request.user.company, f"Produit supprimé : {name}", "trash-can-outline")
        on_commit(lambda: [delete_product_image(path) for path in stale_paths])


class ProductSearchView(ProductListView):
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        category = self.request.query_params.get('category')
        if name:
            queryset = queryset.filter(Q(name__icontains=name) | Q(code__icontains=name))
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        return queryset
