import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from bing.config.models import BInGConfig

logger = logging.getLogger(__name__)


EIGENSCHAP_DATUM = "Vergaderdatum"


class Meeting(models.Model):
    start = models.DateTimeField(_("start"))
    end = models.DateTimeField(_("end"))

    created = models.DateTimeField(_("created"), auto_now_add=True)

    # cross-tracking of case-information
    zaak = models.URLField(_("zaak"), blank=True, max_length=1000, editable=False)

    class Meta:
        verbose_name = _("meeting")
        verbose_name_plural = _("meetings")

    def __str__(self):
        return f"{self.start} - {self.end}"

    def ensure_zaak(self):
        """
        Ensure a 'Zaak' is created for this project.
        """
        if self.zaak:
            return

        # TODO
