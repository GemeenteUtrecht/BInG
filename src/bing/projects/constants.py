from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Toetswijzen(DjangoChoices):
    versneld = ChoiceItem("versneld", _("versneld"))
    regulier = ChoiceItem("regulier", _("regulier"))
    onbekend = ChoiceItem("onbekend", _("weet ik niet"))
