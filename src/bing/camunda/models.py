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


class ProcessDefinition(models.Model):
    camunda_id = models.CharField(_("camunda id"), max_length=100, editable=False)
    key = models.CharField(_("key"), max_length=100, editable=False)
    name = models.CharField(_("name"), max_length=255, editable=False)
    version = models.PositiveSmallIntegerField(_("version"), editable=False)

    class Meta:
        verbose_name = "process definition"
        verbose_name_plural = "process definitions"

    def __str__(self):
        return self.name
