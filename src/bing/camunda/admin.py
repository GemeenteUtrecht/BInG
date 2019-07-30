import functools

from django.contrib import admin
from django.db import transaction
from django.http import HttpRequest

from .forms import DeploymentForm
from .models import Deployment, ProcessDefinition


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "name")
    search_fields = ("name",)
    form = DeploymentForm

    def save_form(self, request: HttpRequest, form: DeploymentForm, change: bool):
        deployment = super().save_form(request, form, change)
        transaction.on_commit(functools.partial(form.update_in_camunda, deployment))
        return deployment


@admin.register(ProcessDefinition)
class ProcessDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "key", "camunda_id")
    search_fields = ("name",)
    list_filter = ("version",)
    ordering = ("name", "-version")
