from django.db import models
from django.utils.translation import ugettext_lazy as _


class Meeting(models.Model):
    start = models.DateTimeField(_("start"))
    end = models.DateTimeField(_("start"))

    projects = models.ManyToManyField("projects.Project", blank=True)

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    class Meta:
        verbose_name = _("meeting")
        verbose_name_plural = _("meetings")
