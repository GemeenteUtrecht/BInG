from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .subscriptions import SUBSCRIPTIONS


class Webhook(models.Model):
    key = models.CharField(
        _("subscription key"),
        max_length=50,
        unique=True,
        choices=sorted([(sub.key, sub.key) for sub in SUBSCRIPTIONS]),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"auth_token__isnull": False},
        on_delete=models.PROTECT,
    )
    _subscription = models.URLField(_("subscription URL"), blank=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["_subscription"],
                condition=~models.Q(_subscription=""),
                name="unique_subscription",
            )
        ]

    def __str__(self):
        return self.key
