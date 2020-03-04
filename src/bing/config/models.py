from datetime import timedelta

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from django_camunda.fields import ProcessDefinitionField
from solo.models import SingletonModel

from bing.projects.constants import Toetswijzen

RSIN = "002220647"


class BInGConfig(SingletonModel):
    """
    BInG-specific configuration
    """

    # TODO: add validator
    organisatie_rsin = models.CharField(
        _("RSIN organisatie"), max_length=9, default="002220647"
    )

    zaaktype_aanvraag = models.URLField(_("Zaaktype aanvraag"))
    zaaktype_vergadering = models.URLField(_("Zaaktype vergadering"))

    minimal_plan_duration = models.DurationField(
        _("minimal duration from aanvraag to vergadering"),
        default=timedelta(days=7),
        help_text=_(
            "De minimale tijd die nodig is tussen het moment van indienen aanvraag "
            "en de eerst mogelijke vergadering."
        ),
    )

    # camunda
    camunda_process = ProcessDefinitionField(_("camunda process to start"), blank=True)

    # BAG interaction
    bag_root = models.URLField(
        default="https://bag.basisregistraties.overheid.nl/api/v1/"
    )
    bag_api_key = models.CharField(_("API key"), max_length=255, blank=True)
    bag_nlx_headers = JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("BInG configuratie")

    def __str__(self):
        return force_text(self._meta.verbose_name)


class RequiredDocuments(models.Model):
    """
    Configure the documents required for a certain Toetswijze
    """

    toetswijze = models.CharField(
        _("toetswijze"), max_length=20, choices=Toetswijzen.choices, unique=True
    )
    informatieobjecttypen = ArrayField(
        models.URLField(_("informatieobjecttype"), max_length=1000),
        blank=False,
        help_text=_("Documenttypen"),
    )

    class Meta:
        verbose_name = _("verplichte documenten")
        verbose_name_plural = _("verplichte documenten")

    def __str__(self):
        return f"{self.get_toetswijze_display()} - {len(self.informatieobjecttypen)} documenten"
