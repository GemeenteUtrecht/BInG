import base64
import json
import logging
import os

from django.utils import timezone

from bing.camunda.client import Camunda
from bing.celery import app
from bing.config.models import BInGConfig
from bing.config.service import get_drc_client
from bing.projects.models import Project, ProjectAttachment

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
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    if project.camunda_process_instance_id and project.camunda_process_instance_url:
        logger.warning("Not re-triggering camunda process for project %s!", project_id)
        return

    config = BInGConfig.get_solo()
    client = Camunda()

    documents = list(project.projectattachment_set.values_list("eio_url", flat=True))

    body = {
        "businessKey": f"bing-project-{project.project_id}",
        "withVariablesInReturn": False,
        "variables": {
            "zaaktype": {"value": config.zaaktype_aanvraag, "type": "String"},
            "project_id": {"value": project.project_id, "type": "String"},
            "datum_ingediend": {
                "value": timezone.now().date().isoformat(),
                "type": "Date",
            },
            "naam": {"value": project.name, "type": "String"},
            "toetswijze": {"value": project.toetswijze, "type": "String"},
            "documenten": {"value": json.dumps(documents), "type": "Json"},
            "meeting_datum": {
                "value": project.meeting.start.date().isoformat()
                if project.meeting_id
                else None,
                "type": "Date",
            },
            "meeting_zaak": {
                "value": project.meeting.zaak if project.meeting_id else None,
                "type": "String",
            },
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
