from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.tenancy import CompanyQuerysetMixin, IsCompanyUser
from .models import Warehouse, StockLocation, StockBalance, StockMovement, InventorySession, InventoryLine
from .serializers import WarehouseSerializer, StockLocationSerializer, StockBalanceSerializer, StockMovementSerializer, InventorySerializer, InventoryCountSerializer
from .services import validate_inventory


class WarehouseViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('name')
    serializer_class = WarehouseSerializer
    permission_classes = [IsCompanyUser]


class StockLocationViewSet(viewsets.ModelViewSet):
    serializer_class = StockLocationSerializer
    permission_classes = [IsCompanyUser]

    def get_queryset(self):
        return StockLocation.objects.filter(warehouse__company=self.request.user.company).order_by('warehouse__name', 'name')

    def perform_create(self, serializer):
        warehouse = serializer.validated_data['warehouse']
        if warehouse.company_id != self.request.user.company_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'warehouse': 'Entrepôt introuvable.'})
        serializer.save()


class StockBalanceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = StockBalanceSerializer
    permission_classes = [IsCompanyUser]

    def get_queryset(self):
        queryset = StockBalance.objects.filter(company=self.request.user.company).select_related('product', 'location')
        product_id = self.request.query_params.get('product')
        location_id = self.request.query_params.get('location')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset.order_by('product__name', 'location__name')


class StockMovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [IsCompanyUser]

    def get_queryset(self):
        return StockMovement.objects.filter(company=self.request.user.company).select_related('product', 'created_by', 'from_location', 'to_location')


class InventoryViewSet(CompanyQuerysetMixin, viewsets.ModelViewSet):
    queryset = InventorySession.objects.all().select_related('warehouse').prefetch_related('lines')
    serializer_class = InventorySerializer
    permission_classes = [IsCompanyUser]

    @transaction.atomic
    def perform_create(self, serializer):
        warehouse = serializer.validated_data['warehouse']
        if warehouse.company_id != self.request.user.company_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'warehouse': 'Entrepôt introuvable.'})
        inventory = serializer.save(company=self.request.user.company, created_by=self.request.user, status=InventorySession.Status.COUNTING)
        balances = StockBalance.objects.filter(company=self.request.user.company, location__warehouse=warehouse).select_related('product', 'location')
        InventoryLine.objects.bulk_create([
            InventoryLine(inventory=inventory, product=balance.product, location=balance.location, expected_quantity=balance.quantity)
            for balance in balances
        ])

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        inventory = self.get_object()
        try:
            validate_inventory(inventory=inventory, actor=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(inventory).data)

    @action(detail=True, methods=['patch'], url_path='lines/(?P<line_id>[^/.]+)')
    def count_line(self, request, pk=None, line_id=None):
        inventory = self.get_object()
        try:
            line = inventory.lines.get(pk=line_id)
        except InventoryLine.DoesNotExist:
            return Response({'detail': 'Ligne introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = InventoryCountSerializer(line, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
