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
        serializer.save(company=self.request.user.company)


class CategoryDetailView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [HasCategoryPermission]


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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(company=request.user.company)
        self._store_images(request, product)
        return Response(ProductSerializer(product, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _store_images(request, product):
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
            ProductImage.objects.create(product=product, url=url, storage_path=storage_path, is_main=index == 0)


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

        if 'images' in request.FILES:
            stale_paths = list(product.images.exclude(storage_path__isnull=True).values_list('storage_path', flat=True))
            product.images.all().delete()
            ProductCreateView._store_images(request, product)
            on_commit(lambda: [delete_product_image(path) for path in stale_paths])
        return Response(ProductSerializer(product, context=self.get_serializer_context()).data)


class ProductDeleteView(CompanyQuerysetMixin, generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasProductPermission]

    def perform_destroy(self, instance):
        stale_paths = list(instance.images.exclude(storage_path__isnull=True).values_list('storage_path', flat=True))
        instance.delete()
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
