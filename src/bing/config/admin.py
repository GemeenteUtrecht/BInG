from django import forms
from django.contrib import admin
from django.contrib.admin import widgets

from solo.admin import SingletonModelAdmin

from bing.camunda.models import ProcessDefinition
from bing.service.ztc import get_aanvraag_iot

from .models import APIConfig, BInGConfig, RequiredDocuments, URLRewrite


@admin.register(APIConfig)
class APIConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(BInGConfig)
class BInGConfigAdmin(SingletonModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "aanvraag_process_key":
            definition_keys = list(
                ProcessDefinition.objects.values_list("key", "name").distinct("key")
            )
            choices = [("", "-------")] + definition_keys
            return forms.ChoiceField(
                label=db_field.verbose_name.capitalize(),
                widget=widgets.AdminRadioSelect(),
                choices=choices,
                required=False,
                help_text=db_field.help_text,
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)


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


@admin.register(URLRewrite)
class URLRewriteAdmin(admin.ModelAdmin):
    list_display = ("from_value", "to_value")
    ordering = ("from_value",)
