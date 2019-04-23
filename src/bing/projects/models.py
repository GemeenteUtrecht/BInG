from django.db import models
from django.utils.translation import ugettext_lazy as _


class Project(models.Model):
    project_id = models.CharField(_("project id"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=50)

    created = models.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")
