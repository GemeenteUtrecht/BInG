from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Toetswijzen(DjangoChoices):
    versneld = ChoiceItem("versneld", _("versneld"))
    regulier = ChoiceItem("regulier", _("regulier"))
    onbekend = ChoiceItem("onbekend", _("weet ik niet"))


class PlanFases(DjangoChoices):
    spve_ipve = ChoiceItem(
        "spve/ipve", _("SPvE/IPvE"), verbose_help=_("Lange uitleg over SPvE/IPvE")
    )
    fo = ChoiceItem("fo", _("FO"), verbose_help=_("Lange uitleg over FO"))
    vo = ChoiceItem("vo", _("VO"), verbose_help=_("Lange uitleg over VO"))
    do = ChoiceItem("do", _("DO"), verbose_help=_("Lange uitleg over VO"))
    onbekend = ChoiceItem("onbekend", _("weet ik niet"))
