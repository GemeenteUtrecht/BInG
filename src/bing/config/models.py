import uuid
from urllib.parse import urljoin

from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel
from zds_client import Client

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
    )
    ztc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    drc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    brc = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = _("APIs configuration")

    def __str__(self):
        return force_text(self._meta.verbose_name)

    def get_drc_client(self) -> Client:
        if not self.drc:
            raise ValueError("No DRC configured!")
        return self.drc.build_client()


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
