from django.contrib import admin # type: ignore

from .models import Discount

admin.site.register(Discount)
