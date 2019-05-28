import logging

from bing.celery import app

from .models import Meeting

logger = logging.getLogger(__name__)


@app.task
def ensure_meeting_zaak(meeting_id: int) -> None:
    try:
        meeting = Meeting.objects.get(id=meeting_id)
    except Meeting.DoesNotExist:
        logger.error("Meeting %d not found in datbaase", meeting_id)
        return
    else:
        meeting.ensure_zaak()
