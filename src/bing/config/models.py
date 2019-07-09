import uuid
from datetime import timedelta
from urllib.parse import urljoin

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel
from zds_client import Client
from zgw_consumers.constants import APITypes

from bing.projects.constants import Toetswijzen

RSIN = "002220647"


def get_client(api_root: str) -> Client:
    dummy_resource = f"dummy/{uuid.uuid4()}"
    full_url = urljoin(api_root, dummy_resource)
    return Client.from_url(full_url)


class APIConfig(SingletonModel):
    zrc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        limit_choices_to={"api_type": APITypes.zrc},
    )
    ztc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        limit_choices_to={"api_type": APITypes.ztc},
    )
    drc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        limit_choices_to={"api_type": APITypes.drc},
    )
    brc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        limit_choices_to={"api_type": APITypes.brc},
    )

    class Meta:
        verbose_name = _("APIs configuration")

    def __str__(self):
        return force_text(self._meta.verbose_name)


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


class URLRewrite(models.Model):
    from_value = models.CharField(_("from value"), max_length=100, unique=True)
    to_value = models.CharField(_("to value"), max_length=100)

    class Meta:
        verbose_name = _("URL rewrite")
        verbose_name_plural = _("URL rewrites")

    def __str__(self):
        return f"{self.from_value} -> {self.to_value}"
