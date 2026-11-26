from django.contrib import admin
from .models import WatchedItem


@admin.register(WatchedItem)
class WatchedItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_type', 'item_id', 'item_label', 'created_at']
    list_filter = ['item_type']
    search_fields = ['item_label', 'user__username']
