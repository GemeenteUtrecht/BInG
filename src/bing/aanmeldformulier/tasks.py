import base64
import logging
import os

from django.utils import timezone

from bing.celery import app
from bing.config.models import BInGConfig
from bing.config.service import get_drc_client
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
            # TODO: This should not be set here by default. Please have a look at issue 224 for more information.
            # https://github.com/GemeenteUtrecht/ZGW/issues/224
            "indicatie_gebruiksrecht": False,
        },
    )

    attachment.eio_url = eio["url"]
    attachment.save(update_fields=["eio_url"])

    os.remove(temp_file)


@app.task
def start_camunda_process(project_id: int) -> None:
    pass
