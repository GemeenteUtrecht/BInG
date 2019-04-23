from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_id", "name")
    list_filter = ("created",)
    search_fields = ("project_id", "name")
