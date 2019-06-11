from django import forms
from django.contrib import admin

from solo.admin import SingletonModelAdmin

from bing.service.ztc import get_aanvraag_iot

from .models import APIConfig, BInGConfig, RequiredDocuments


@admin.register(APIConfig)
class APIConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(BInGConfig)
class BInGConfigAdmin(SingletonModelAdmin):
    pass


def get_informatieobjecttype_choices() -> list:
    return [("foo", "bar")]


@admin.register(RequiredDocuments)
class RequiredDocumentsAdmin(admin.ModelAdmin):
    list_display = ("toetswijze", "num_informatieobjecttypen")
    list_filter = ("toetswijze",)
    search_fields = ("informatieobjecttypen",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "informatieobjecttypen":
            choices = get_aanvraag_iot()
            return forms.MultipleChoiceField(
                label=db_field.verbose_name.capitalize(),
                widget=forms.CheckboxSelectMultiple(),
                choices=choices,
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def num_informatieobjecttypen(self, obj):
        return len(obj.informatieobjecttypen)

    num_informatieobjecttypen.short_description = "# informatieobjecttypen"
