from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import APIConfig, BInGConfig


@admin.register(APIConfig)
class APIConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (_("DRC"), {"fields": ("drc_api_root", "drc_client_id", "drc_secret")}),
    )


@admin.register(BInGConfig)
class BInGConfigAdmin(SingletonModelAdmin):
    pass
