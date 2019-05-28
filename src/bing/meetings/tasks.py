import logging

from bing.celery import app
from bing.config.service import get_zrc_client
from bing.projects.models import Project

from .models import Meeting

logger = logging.getLogger(__name__)


@app.task
def ensure_meeting_zaak(meeting_id: int) -> None:
    try:
        meeting = Meeting.objects.get(id=meeting_id)
    except Meeting.DoesNotExist:
        logger.error("Meeting %d not found in database", meeting_id)
        return
    else:
        meeting.ensure_zaak()


@app.task
def add_project_to_meeting(meeting_id: int, project_id: int) -> None:
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        project = Project.objects.get(id=project_id)
    except Meeting.DoesNotExist:
        logger.error("Meeting %d not found in database", meeting_id)
        return
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    project.ensure_zaak()

    zrc_client = get_zrc_client(
        scopes=["zds.scopes.zaken.aanmaken", "zds.scopes.zaken.bijwerken"]
    )

    # fetch the current zaak so we can add gerelateerde zaken
    zaak = zrc_client.retrieve("zaak", url=meeting.zaak)
    relevant_andere_zaken = zaak["relevanteAndereZaken"] + [project.zaak]

    # TODO: E-tag logic for concurrent updates
    zrc_client.partial_update(
        "zaak", {"relevanteAndereZaken": relevant_andere_zaken}, url=meeting.zaak
    )
