from django.contrib import admin # type: ignore

from .models import Supplier

admin.site.register(Supplier)