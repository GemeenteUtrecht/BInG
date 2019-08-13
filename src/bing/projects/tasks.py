import base64
import json
import logging
import os

from django.utils import timezone

from celery.result import AsyncResult, ResultSet

from bing.camunda.client import Camunda
from bing.celery import app
from bing.config.models import BInGConfig
from bing.config.service import get_drc_client
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
def start_camunda_process(project_id: int) -> None:
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
        start_camunda_process.apply_async(args=(project_id,), countdown=1.0)
        return

    if project.camunda_process_instance_id and project.camunda_process_instance_url:
        logger.warning("Not re-triggering camunda process for project %s!", project_id)
        return

    config = BInGConfig.get_solo()
    client = Camunda()

    documents = [attachment["eio_url"] for attachment in attachments]

    body = {
        "businessKey": f"bing-project-{project.project_id}",
        "withVariablesInReturn": False,
        "variables": {
            "zaak": {
                "type": "Json",
                "value": json.dumps(
                    {
                        "bronorganisatie": config.organisatie_rsin,
                        "identificatie": project.zaak_identificatie,
                        "zaaktype": config.zaaktype_aanvraag,
                        "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                        "startdatum": timezone.now().date().isoformat(),
                        "omschrijving": f"BInG aanvraag voor {project.name}",
                    }
                ),
            },
            "projectId": {"value": project.project_id, "type": "String"},
            "toetswijze": {"value": project.toetswijze, "type": "String"},
            "documenten": {"value": json.dumps(documents), "type": "Json"},
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
