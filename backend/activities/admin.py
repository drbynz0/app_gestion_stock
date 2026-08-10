from django.contrib import admin # type: ignore

from .models import Activity

admin.site.register(Activity)
