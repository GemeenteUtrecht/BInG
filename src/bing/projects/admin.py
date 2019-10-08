from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _

from .models import Project, ProjectAttachment
from .tasks import relate_created_zaak, start_camunda_process


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_id", "name", "zaak", "camunda_process_instance_url")
    list_filter = ("created", "meeting")
    search_fields = ("project_id", "name", "zaak")
    actions = ["_start_camunda_process", "_relate_created_zaak"]

    def _start_camunda_process(
        self, request: HttpRequest, queryset: models.QuerySet
    ) -> None:
        for project in queryset:
            start_camunda_process(project.id)
            # start_camunda_process.delay(project.id)
        self.message_user(
            request,
            _("Started the Camunda process for {count} projects").format(
                count=queryset.count()
            ),
        )

    _start_camunda_process.short_description = _("Start Camunda proces")

    def _relate_created_zaak(
        self, request: HttpRequest, queryset: models.QuerySet
    ) -> None:
        for project in queryset:
            relate_created_zaak(project.id)
        self.message_user(request, _("Retrieved the zaak references for each project."))

    _relate_created_zaak.short_description = _("Relate the created Zaak objects")


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ("project", "eio_url", "celery_task_id")
    list_filter = ("project",)
    list_select_related = ("project",)
