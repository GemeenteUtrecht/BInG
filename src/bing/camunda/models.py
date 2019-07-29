from django.db import models
from django.utils.translation import ugettext_lazy as _


class Deployment(models.Model):
    uuid = models.UUIDField(_("id"), unique=True, editable=False)
    name = models.CharField(_("name"), max_length=255, blank=True)

    class Meta:
        verbose_name = "deployment"
        verbose_name_plural = "deployments"

    def __str__(self):
        return self.name
