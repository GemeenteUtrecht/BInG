from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client

from .constants import Toetswijzen


class Project(models.Model):
    project_id = models.CharField(_("project id"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=50)

    toetswijze = models.CharField(
        _("toetswijze"), max_length=20, choices=Toetswijzen.choices
    )

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return f"{self.project_id} | {self.name}"

    def ensure_zaak(self):
        """
        Ensure a 'Zaak' is created for this project.
        """
        if self.zaak:
            return

        config = BInGConfig.get_solo()
        client = get_zrc_client(scopes=["zds.scopes.zaken.aanmaken"])

        # TODO: fill in einddatumGepland etc.

        zaak = client.create(
            "zaak",
            {
                "bronorganisatie": config.organisatie_rsin,
                "identificatie": f"BING-{self.project_id}",
                "zaaktype": config.zaaktype_aanvraag,
                "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                "startdatum": timezone.localdate(self.created).isoformat(),
                "omschrijving": f"BInG aanvraag voor {self.name}",
            },
        )

        self.zaak = zaak["url"]
        self.save(update_fields=("zaak",))


class ProjectAttachment(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)

    io_type = models.URLField(_("document type"), blank=True)
    eio_url = models.URLField(_("enkelvoudig informatieobject URL"), blank=True)

    class Meta:
        verbose_name = _("project attachment")
        verbose_name_plural = _("project attachments")
