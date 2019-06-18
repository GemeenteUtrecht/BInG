import base64
import logging
import os

from django.utils import timezone

from zds_client import ClientError

from bing.celery import app
from bing.config.models import BInGConfig
from bing.config.service import get_drc_client, get_zrc_client
from bing.projects.models import ProjectAttachment

logger = logging.getLogger(__name__)


@app.task
def add_project_attachment(attachment_id: int, filename: str, temp_file: str):
    try:
        attachment = ProjectAttachment.objects.select_related("project").get(
            id=attachment_id
        )
    except ProjectAttachment.DoesNotExist:
        logger.warning("Could not fetch ProjectAttachment %d", attachment_id)
        return

    config = BInGConfig.get_solo()

    with open(temp_file, "rb") as infile:
        content = infile.read()

    io_type = attachment.io_type

    # create informatieobject
    drc_client = get_drc_client(scopes=["zds.scopes.documenten.aanmaken"])
    eio = drc_client.create(
        "enkelvoudiginformatieobject",
        {
            "bronorganisatie": config.organisatie_rsin,
            "informatieobjecttype": io_type,
            "creatiedatum": timezone.now().date().isoformat(),
            "bestandsnaam": filename,
            "titel": os.path.splitext(filename)[0],
            "auteur": "BInG formulier",
            "taal": "dut",
            "inhoud": base64.b64encode(content).decode("ascii"),
        },
    )

    attachment.io_type = io_type
    attachment.eio_url = eio["url"]

    # connect io and zaak
    try:
        drc_client.create(
            "objectinformatieobject",
            {
                "informatieobject": eio["url"],
                "object": attachment.project.zaak,
                "objectType": "zaak",
                "beschrijving": "Aangeleverd stuk door aanvrager",
            },
        )
    except ClientError as exc:
        logger.info("Trying new setup, got %s", exc)
        # try the new setup, with reversal of relation direction
        zrc_client = get_zrc_client()
        zrc_client.create(
            "zaakinformatieobject",
            {
                "zaak": attachment.project.zaak,
                "informatieobject": eio["url"],
                "beschrijving": "Aangeleverd stuk door aanvrager",
            },
        )

    os.remove(temp_file)
