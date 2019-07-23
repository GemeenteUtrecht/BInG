from django.contrib import admin

from .models import CachedResource


@admin.register(CachedResource)
class CachedResourceAdmin(admin.ModelAdmin):
    list_display = ("url", "created", "updated")
    search_fields = ("url", "created", "updated")
    date_hierarchy = "created"
