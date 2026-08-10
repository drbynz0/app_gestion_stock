from django.contrib import admin # type: ignore

from .models import FactureClient, FactureFournisseur

admin.site.register(FactureClient)
admin.site.register(FactureFournisseur)
