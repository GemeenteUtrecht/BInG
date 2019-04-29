from django.db import models
from django.utils.translation import ugettext_lazy as _

from .constants import Toetswijzen


class Project(models.Model):
    project_id = models.CharField(_("project id"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=50)

    toetswijze = models.CharField(
        _("toetswijze"), max_length=20, choices=Toetswijzen.choices
    )

    created = models.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return f"{self.project_id} | {self.name}"


class ProjectAttachment(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)

    io_type = models.URLField(_("document type"), blank=True)
    eio_url = models.URLField(_("enkelvoudig informatieobject URL"), blank=True)

    class Meta:
        verbose_name = _("project attachment")
        verbose_name_plural = _("project attachments")
