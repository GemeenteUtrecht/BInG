import logging

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client, get_ztc_client

logger = logging.getLogger(__name__)


EIGENSCHAP_DATUM = "Vergaderdatum"


class Meeting(models.Model):
    start = models.DateTimeField(_("start"))
    end = models.DateTimeField(_("start"))

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    class Meta:
        verbose_name = _("meeting")
        verbose_name_plural = _("meetings")

    def __str__(self):
        return f"{self.start} - {self.end}"

    def ensure_zaak(self):
        """
        Ensure a 'Zaak' is created for this project.
        """
        if self.zaak:
            return

        config = BInGConfig.get_solo()
        zrc_client = get_zrc_client(
            scopes=["zds.scopes.zaken.aanmaken", "zds.scopes.zaken.bijwerken"],
            zaaktypen=[config.zaaktype_vergadering],
        )
        ztc_client = get_ztc_client()

        zaaktype_url = config.zaaktype_vergadering
        zaaktype = ztc_client.retrieve("zaaktype", url=zaaktype_url)

        bits = zaaktype_url.split("/")
        catalogus_uuid = bits[-3]
        zaaktype_uuid = bits[-1]

        eigenschappen = ztc_client.list(
            "eigenschap", catalogus_uuid=catalogus_uuid, zaaktype_uuid=zaaktype_uuid
        )
        eigenschap = next(
            eigenschap
            for eigenschap in eigenschappen
            if eigenschap["naam"] == EIGENSCHAP_DATUM
        )

        start_date = timezone.make_naive(self.start).date()
        end_date = timezone.make_naive(self.end).date()

        zaak = zrc_client.create(
            "zaak",
            {
                "bronorganisatie": config.organisatie_rsin,
                "identificatie": f"BiNG-vergadering-{start_date.isoformat()}",
                "zaaktype": zaaktype_url,
                "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                "startdatum": start_date.isoformat(),
                "omschrijving": f"BInG vergadering",
                "einddatumGepland": end_date.isoformat(),
            },
        )

        zaak_uuid = zaak["url"].split("/")[-1]
        self.zaak = zaak["url"]
        self.save(update_fields=("zaak",))

        zrc_client.create(
            "zaakeigenschap",
            {
                "zaak": zaak["url"],
                "eigenschap": eigenschap["url"],
                "waarde": start_date.isoformat(),
            },
            zaak_uuid=zaak_uuid,
        )

        # set the initial status
        if not zaaktype["statustypen"]:
            logger.warning("Zaaktype %s has no statustypen!", zaaktype_url)
            return

        status_type = zaaktype["statustypen"][0]
        zrc_client.create(
            "status",
            {
                "zaak": self.zaak,
                "statusType": status_type,
                "datumStatusGezet": timezone.localtime().isoformat(),
                "statustoelichting": "Aanvraag ingediend",
            },
        )
