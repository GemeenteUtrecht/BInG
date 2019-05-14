import uuid
from urllib.parse import urljoin

from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel
from zds_client import Client
from zgw_consumers.constants import APITypes

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

    class Meta:
        verbose_name = _("BInG configuratie")

    def __str__(self):
        return force_text(self._meta.verbose_name)
