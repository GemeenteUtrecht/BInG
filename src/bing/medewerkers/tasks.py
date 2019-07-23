import base64
import logging
import os

from django.utils import timezone

from bing.config.models import BInGConfig
from bing.config.service import get_brc_client, get_drc_client, get_ztc_client
from bing.projects.models import Project
from bing.service.zrc import set_resultaat, set_status

from ..celery import app

logger = logging.getLogger(__name__)


@app.task()
def set_new_status(zaak_url: str, status_type: str) -> None:
    set_status(zaak_url, status_type)


@app.task()
def set_result(zaak_url: str, resultaat_type: str) -> None:
    set_resultaat(zaak_url, resultaat_type)


@app.task()
def add_besluit(
    project_id: int, filename: str, temp_file: str, besluittype: str, **extra
):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    with open(temp_file, "rb") as infile:
        content = infile.read()

    config = BInGConfig.get_solo()
    ztc_client = get_ztc_client()
    drc_client = get_drc_client(scopes=["zds.scopes.documenten.aanmaken"])
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.aanmaken"])

    # register the document
    besluittype = ztc_client.retrieve("besluittype", url=besluittype)
    io_type = besluittype["informatieobjecttypes"][0]

    today = timezone.now().date().isoformat()

    eio = drc_client.create(
        "enkelvoudiginformatieobject",
        {
            "bronorganisatie": config.organisatie_rsin,
            "informatieobjecttype": io_type,
            "creatiedatum": today,
            "bestandsnaam": filename,
            "titel": os.path.splitext(filename)[0],
            "auteur": "BInG Secretaris",
            "taal": "dut",
            "inhoud": base64.b64encode(content).decode("ascii"),
            # TODO: This should not be set here by default. Please have a look at issue 224 for more information.
            # https://github.com/GemeenteUtrecht/ZGW/issues/224
            "indicatie_gebruiksrecht": False,
        },
    )
    logger.debug("Created EIO %r", eio)

    # create the besluit
    besluit_data = {
        "verantwoordelijkeOrganisatie": config.organisatie_rsin,
        "besluittype": besluittype["url"],
        "zaak": project.zaak,
        "datum": today,
    }
    besluit_data.update(**extra)
    besluit = brc_client.create("besluit", besluit_data)
    logger.debug("Created BESLUIT %r", besluit)

    # create BesluitInformatieObject
    drc_client.create(
        "objectinformatieobject",
        {
            "informatieobject": eio["url"],
            "object": besluit["url"],
            "objectType": "besluit",
            "beschrijving": "Besluit opgesteld tijdens vergadering",
        },
    )

    os.remove(temp_file)
