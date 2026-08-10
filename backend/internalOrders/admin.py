from django.contrib import admin # type: ignore

from .models import InternalOrder, OrderItem

admin.site.register(InternalOrder)
admin.site.register(OrderItem)
