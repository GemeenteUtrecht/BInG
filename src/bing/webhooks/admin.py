from django.contrib import admin

from .models import Webhook


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "_subscription")
    search_fields = ("key",)
