from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _


class CachedResource(models.Model):
    url = models.URLField(
        _("url"), help_text=_("Uniquely identifying resource URL"), unique=True
    )
    resource = JSONField(_("resource"))

    created = models.DateTimeField(_("created"), auto_now_add=True)
    updated = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        verbose_name = _("cached resource")
        verbose_name_plural = _("cached resources")

    def __str__(self):
        return self.url
