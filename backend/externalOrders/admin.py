from django.contrib import admin # type: ignore

from .models import ExternalOrder, OrderItem

admin.site.register(ExternalOrder)
admin.site.register(OrderItem)
