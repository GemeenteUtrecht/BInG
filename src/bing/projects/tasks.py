import base64
import json
import logging
import os

from django.utils import timezone

from celery.result import AsyncResult, ResultSet

from bing.camunda.client import Camunda
from bing.camunda.interface import DocumentListVariable, ZaakVariable
from bing.celery import app
from bing.config.models import BInGConfig
from bing.config.service import get_drc_client, get_zrc_client
from bing.projects.models import Project, ProjectAttachment

logger = logging.getLogger(__name__)


@app.task
def upload_document(attachment_id: int, filename: str, temp_file: str):
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
def start_camunda_process(project_id: int, attempt=0) -> None:
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    attachments = list(
        project.projectattachment_set.values("eio_url", "celery_task_id")
    )

    # check that the file uploads have completed
    results = [
        AsyncResult(str(attachment["celery_task_id"])) for attachment in attachments
    ]
    group_result = ResultSet(results=results)
    if not group_result.ready():
        # prevent endless scheduled tasks if the result is purged from the redis
        # storage - which would result in state PENDING
        if attempt >= 5:
            logger.error("Attempted process start %d times, giving up", attempt)
            return
        start_camunda_process.apply_async(
            args=(project_id,), kwargs={"attempt": attempt + 1}, countdown=2 ** attempt
        )
        return

    if project.camunda_process_instance_id and project.camunda_process_instance_url:
        logger.warning("Not re-triggering camunda process for project %s!", project_id)
        return

    config = BInGConfig.get_solo()
    client = Camunda()

    documents = [attachment["eio_url"] for attachment in attachments]

    body = {
        "businessKey": f"bing-aanvraag",
        "withVariablesInReturn": False,
        "variables": {
            "zaak": ZaakVariable(
                data={
                    "bronorganisatie": config.organisatie_rsin,
                    "identificatie": project.zaak_identificatie,
                    "zaaktype": config.zaaktype_aanvraag,
                    "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                    "startdatum": timezone.now().date().isoformat(),
                    "omschrijving": f"BInG aanvraag voor {project.name}",
                }
            ).serialize(),
            "projectId": {"value": project.project_id, "type": "String"},
            "toetswijze": {"value": project.toetswijze, "type": "String"},
            "documenten": DocumentListVariable(data=documents).serialize(),
        },
    }

    response = client.request(
        f"process-definition/key/{config.aanvraag_process_key}/start",
        method="POST",
        json=body,
    )

    project.camunda_process_instance_id = response["id"]

    self_rel = next((link for link in response["links"] if link["rel"] == "self"))
    project.camunda_process_instance_url = self_rel["href"]
    project.save(
        update_fields=["camunda_process_instance_id", "camunda_process_instance_url"]
    )

    relate_created_zaak.delay(project_id)


@app.task
def relate_created_zaak(project_id: int):
    """
    Fetch the created Zaak object and relate it to the project.
    """
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    assert (
        project.camunda_process_instance_id
    ), "Project must have a Camunda process instance"

    if project.zaak:
        return

    client = Camunda()
    response = client.request(
        f"process-instance/{project.camunda_process_instance_id}/variables",
        params={"deserializeValues": "false"},
    )

    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(
        scopes=["zds.scopes.zaken.lezen", "zds.scopes.zaken.bijwerken"],
        zaaktypes=[config.zaaktype_aanvraag, config.zaaktype_vergadering],
    )

    zaak_uuid = json.loads(response["zaak_id"]["value"])
    zaak = zrc_client.retrieve("zaak", uuid=zaak_uuid)

    # TODO: should be respected by Camunda in the first place
    # fix the identificatie
    zrc_client.partial_update(
        "zaak",
        {
            "identificatie": project.zaak_identificatie,
            "omschrijving": f"BInG aanvraag voor {project.name}",
        },
        uuid=zaak_uuid,
    )

    project.zaak = zaak["url"]
    project.save(update_fields=["zaak"])
