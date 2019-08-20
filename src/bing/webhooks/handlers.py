import logging

from bing.config.service import get_zrc_client
from bing.projects.models import Project
from bing.projects.utils import match_project_id

logger = logging.getLogger(__name__)


def update_project_for_new_zaak(zaak_url: str):
    client = get_zrc_client(scopes=["zds.scopes.zaken.lezen"])
    try:
        zaak = client.retrieve("zaak", url=zaak_url)
    except Exception:
        logger.exception("Could not retrieve zaak %s", zaak)
        return

    project_id = match_project_id(zaak["identificatie"])
    if not project_id:
        logger.info(
            "Zaak doesn't seem to be a BInG aanvraag (unexpected identification). Zaak: %r",
            zaak,
        )
        return

    try:
        project = Project.objects.get(project_id=project_id)
    except Project.DoesNotExist:
        logger.info(
            "Couldn't find the project for zaak %s in the local database",
            zaak["identificatie"],
        )
        return

    project.zaak = zaak_url
    project.save(update_fields=["zaak"])
