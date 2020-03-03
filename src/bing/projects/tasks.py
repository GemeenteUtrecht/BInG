import json
import logging

from django.utils import timezone

from django_camunda.client import get_client
from django_camunda.tasks import start_process

from bing.celery import app
from bing.config.models import BInGConfig
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

    # FIXME upload files


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
    if not config.camunda_process:
        logger.error("Camunda process definition is not configured")
        return

    # TODO add uploaded documents

    variables = {
        "organisatieRSIN": {"value": config.organisatie_rsin, "type": "String"},
        "zaaktype": {"value": config.zaaktype_aanvraag, "type": "String"},
        "projectId": {"value": project.project_id, "type": "String"},
        "toetswijze": {"value": project.toetswijze, "type": "String"},
    }

    process_instance = start_process(
        process_id=config.camunda_process,
        business_key="bing-aanvraag",
        variables=variables,
    )

    project.camunda_process_instance_id = process_instance["instance_id"]
    project.camunda_process_instance_url = process_instance["instance_url"]
    project.save(
        update_fields=["camunda_process_instance_id", "camunda_process_instance_url"]
    )

    # TODO fetch zaak
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

    client = get_client()
    variables = client.request(
        f"process-instance/{project.camunda_process_instance_id}/variables",
        params={"deserializeValues": "false"},
        underscoreize=False,
    )
    if "zaak" in variables:
        assert variables["zaak"]["type"] == "Json"
        zaak = json.loads(variables["zaak"]["value"])

        project.zaak = zaak["zaakUrl"]
        project.save(update_fields=["zaak"])
