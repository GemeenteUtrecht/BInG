import concurrent.futures
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from zds_client.client import ClientError

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client, get_ztc_client
from bing.service.drc import fetch_document
from bing.service.zrc import fetch_zaak
from bing.service.ztc import get_aanvraag_iot

from .constants import PlanFases, Toetswijzen

logger = logging.getLogger(__name__)


class Project(models.Model):
    project_id = models.CharField(_("project id"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=50)

    toetswijze = models.CharField(
        _("toetswijze"), max_length=20, choices=Toetswijzen.choices
    )
    planfase = models.CharField(_("planfase"), max_length=20, choices=PlanFases.choices)

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    # which meeting is it planned on?
    meeting = models.ForeignKey(
        "meetings.Meeting",
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
        verbose_name=_("meeting"),
        help_text=_("Specify during which meeting the project will be discussed."),
    )

    # track camunda references
    camunda_process_instance_id = models.CharField(
        _("process instance ID"), max_length=100, unique=True, blank=True
    )
    camunda_process_instance_url = models.URLField(
        _("process instance URL"), unique=True, blank=True
    )

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
        zrc_client = get_zrc_client(
            scopes=["zds.scopes.zaken.aanmaken"], zaaktypes=[config.zaaktype_aanvraag]
        )
        ztc_client = get_ztc_client()

        # TODO: fill in einddatumGepland etc.

        zaaktype_url = config.zaaktype_aanvraag
        startdatum = timezone.localdate(self.created).isoformat()

        zaak = zrc_client.create(
            "zaak",
            {
                "bronorganisatie": config.organisatie_rsin,
                "identificatie": f"BING-{self.project_id}",
                "zaaktype": zaaktype_url,
                "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                "startdatum": startdatum,
                "omschrijving": f"BInG aanvraag voor {self.name}",
            },
        )

        self.zaak = zaak["url"]
        self.save(update_fields=("zaak",))

        # set the initial status
        zaaktype = ztc_client.retrieve("zaaktype", url=zaaktype_url)
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

    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve a list of attachments
        """
        attachments = self.projectattachment_set.exclude(io_type="").exclude(eio_url="")
        if not attachments:
            return []

        # fetch existing files to display
        document_types = dict(get_aanvraag_iot())

        def _get_document(attachment: ProjectAttachment) -> Dict[str, Any]:
            try:
                document = fetch_document(url=attachment.eio_url)
            except ClientError:
                return None
            else:
                return {
                    "document_type": document_types[attachment.io_type],
                    "informatieobject": document,
                    "attachment": attachment,
                }

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(attachments))
        documents = list(pool.map(_get_document, attachments))
        return list(filter(None, documents))

    def get_meeting_date(self) -> Optional[datetime]:
        """
        Determine the date of the meeting this project is planned in.
        """
        # no zaak created yet -> it cannot possibly be a related zaak
        if not self.zaak:
            return None

        # no meeting assigned -> not planned
        if not self.meeting_id:
            return None

        # no zaak created yet for the meeting
        if not self.meeting.zaak:
            return None

        vergader_zaak = fetch_zaak(url=self.meeting.zaak)
        # only confirmed if it's a related case
        if self.zaak not in vergader_zaak["relevanteAndereZaken"]:
            return None

        return self.meeting.start

    def notify(self, msg: str):
        logger.info("BInG-aanvraag notificatie: %s", msg)


class ProjectAttachment(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)

    io_type = models.URLField(_("document type"), blank=True)
    eio_url = models.URLField(_("enkelvoudig informatieobject URL"), blank=True)

    class Meta:
        verbose_name = _("project attachment")
        verbose_name_plural = _("project attachments")
