from django.contrib import admin

from django_camunda.admin import CamundaFieldsMixin
from solo.admin import SingletonModelAdmin

from .models import BInGConfig, RequiredDocuments


@admin.register(BInGConfig)
class BInGConfigAdmin(CamundaFieldsMixin, SingletonModelAdmin):
    pass


@admin.register(RequiredDocuments)
class RequiredDocumentsAdmin(admin.ModelAdmin):
    list_display = ("toetswijze", "num_informatieobjecttypen")
    list_filter = ("toetswijze",)
    search_fields = ("informatieobjecttypen",)

    def num_informatieobjecttypen(self, obj):
        return len(obj.informatieobjecttypen)

    num_informatieobjecttypen.short_description = "# informatieobjecttypen"
