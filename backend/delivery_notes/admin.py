from django.contrib import admin # type: ignore

from .models import DeliveryNote, DeliveryItem

admin.site.register(DeliveryNote)
admin.site.register(DeliveryItem)
