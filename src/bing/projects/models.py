import logging
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_camunda.models import ProcessInstanceMixin

from .constants import PlanFases, Toetswijzen

logger = logging.getLogger(__name__)


class Project(ProcessInstanceMixin, models.Model):
    project_id = models.CharField(_("project id"), max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=50)

    toetswijze = models.CharField(
        _("toetswijze"), max_length=20, choices=Toetswijzen.choices
    )
    planfase = models.CharField(_("planfase"), max_length=20, choices=PlanFases.choices)

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    # which meeting is it planned on?
    meeting = models.ForeignKey(
        "meetings.Meeting",
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
        verbose_name=_("meeting"),
        help_text=_("Specify during which meeting the project will be discussed."),
    )

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return f"{self.project_id} | {self.name}"

    @property
    def zaak_identificatie(self) -> str:
        return f"BInG-{self.project_id}"

    def ensure_zaak(self):
        """
        Ensure a 'Zaak' is created for this project.
        """
        warnings.warn(
            "The ZAAK object should be created via Camunda", DeprecationWarning
        )

        # TODO
        if self.zaak:
            return

    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve a list of attachments
        """
        attachments = self.projectattachment_set.exclude(io_type="").exclude(eio_url="")
        if not attachments:
            return []

        # TODO

        return []

    def get_meeting_date(self) -> Optional[datetime]:
        """
        Determine the date of the meeting this project is planned in.
        """
        # no zaak created yet -> it cannot possibly be a related zaak
        if not self.zaak:
            return None

        # no meeting assigned -> not planned
        if not self.meeting_id:
            return None

        # no zaak created yet for the meeting
        if not self.meeting.zaak:
            return None

        # TODO only confirmed if it's a related case

        return self.meeting.start

    def notify(self, msg: str):
        logger.info("BInG-aanvraag notificatie: %s", msg)


class ProjectAttachment(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)

    io_type = models.URLField(_("document type"), blank=True)
    eio_url = models.URLField(_("enkelvoudig informatieobject URL"), blank=True)

    celery_task_id = models.UUIDField(
        _("celery task id"), editable=False, blank=True, null=True
    )

    class Meta:
        verbose_name = _("project attachment")
        verbose_name_plural = _("project attachments")
