from django.contrib import admin

from .models import Project, ProjectAttachment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_id", "name")
    list_filter = ("created",)
    search_fields = ("project_id", "name")


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ("project", "eio_url")
    list_filter = ("project",)
    list_select_related = ("project",)
