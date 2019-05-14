from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import APIConfig, BInGConfig


@admin.register(APIConfig)
class APIConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(BInGConfig)
class BInGConfigAdmin(SingletonModelAdmin):
    pass
