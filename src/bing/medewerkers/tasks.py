import logging

from bing.projects.models import Project
from bing.service.zrc import set_status

from ..celery import app

logger = logging.getLogger(__name__)


@app.task()
def set_new_status(project_id: int, status_type: str) -> None:
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("Project %d not found in database", project_id)
        return

    assert project.zaak, "Project did not have a zaak!"

    set_status(project.zaak, status_type)
