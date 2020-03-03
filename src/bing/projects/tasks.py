import logging

from django.utils import timezone

from celery.result import AsyncResult, ResultSet
from django_camunda.client import get_client

from bing.camunda.interface import DocumentListVariable, ZaakVariable
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

    # TODO upload files


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
    client = get_client()

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

    client = get_client()
    response = client.request(
        f"process-instance/{project.camunda_process_instance_id}/variables",
        params={"deserializeValues": "false"},
    )

    config = BInGConfig.get_solo()

    # TODO fetch zaak

    project.zaak = ""
    project.save(update_fields=["zaak"])
