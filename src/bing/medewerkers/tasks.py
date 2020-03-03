import logging

from bing.config.models import BInGConfig
from bing.projects.models import Project

from ..celery import app

logger = logging.getLogger(__name__)


@app.task()
def set_new_status(zaak_url: str, status_type: str) -> None:
    # FIXME add status
    # set_status(zaak_url, status_type)
    pass


@app.task()
def set_result(zaak_url: str, resultaat_type: str) -> None:
    # FIXME add resultaat
    # set_resultaat(zaak_url, resultaat_type)
    pass


@app.task()
def add_besluit(
    project_id: int, filename: str, temp_file: str, besluittype: str, **extra
):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    config = BInGConfig.get_solo()

    # FIXME register the document
    # besluittype = ztc_client.retrieve("besluittype", url=besluittype)
    # io_type = besluittype["informatieobjecttypes"][0]
    #
    # today = timezone.now().date().isoformat()
    #
    # eio = drc_client.create(
    #     "enkelvoudiginformatieobject",
    #     {
    #         "bronorganisatie": config.organisatie_rsin,
    #         "informatieobjecttype": io_type,
    #         "creatiedatum": today,
    #         "bestandsnaam": filename,
    #         "titel": os.path.splitext(filename)[0],
    #         "auteur": "BInG Secretaris",
    #         "taal": "dut",
    #         "inhoud": base64.b64encode(content).decode("ascii"),
    #         # TODO: This should not be set here by default. Please have a look at issue 224 for more information.
    #         # https://github.com/GemeenteUtrecht/ZGW/issues/224
    #         "indicatie_gebruiksrecht": False,
    #     },
    # )
    # logger.debug("Created EIO %r", eio)
    #
    # # create the besluit
    # besluit_data = {
    #     "verantwoordelijkeOrganisatie": config.organisatie_rsin,
    #     "besluittype": besluittype["url"],
    #     "zaak": project.zaak,
    #     "datum": today,
    # }
    # besluit_data.update(**extra)
    # besluit = brc_client.create("besluit", besluit_data)
    # logger.debug("Created BESLUIT %r", besluit)
    #
    # # create BesluitInformatieObject
    # drc_client.create(
    #     "objectinformatieobject",
    #     {
    #         "informatieobject": eio["url"],
    #         "object": besluit["url"],
    #         "objectType": "besluit",
    #         "beschrijving": "Besluit opgesteld tijdens vergadering",
    #     },
    # )
    #
