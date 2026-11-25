from django.contrib import admin
from .models import Warehouse, StockLocation, StockBalance, StockMovement, InventorySession, InventoryLine


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'company')
    search_fields = ('name', 'code')


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'warehouse', 'is_active')
    list_filter = ('is_active', 'warehouse__company')
    search_fields = ('name', 'code')


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'quantity', 'company', 'updated_at')
    list_filter = ('company', 'location__warehouse')
    search_fields = ('product__name', 'location__name')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'from_location', 'to_location', 'company', 'created_at')
    list_filter = ('movement_type', 'company', 'created_at')
    search_fields = ('product__name', 'reference', 'reason')


class InventoryLineInline(admin.TabularInline):
    model = InventoryLine
    extra = 0


@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'warehouse', 'status', 'company', 'created_by', 'created_at', 'validated_at')
    list_filter = ('status', 'company', 'created_at')
    search_fields = ('name', 'warehouse__name')
    inlines = [InventoryLineInline]
