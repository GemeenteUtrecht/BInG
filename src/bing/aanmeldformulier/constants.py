from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

from bing.projects.constants import Toetswijzen

PROJECT_SESSION_KEY = "project_id"


class Steps(DjangoChoices):
    info = ChoiceItem("info", _("Projectinfo"))
    toetswijze = ChoiceItem("toetswijze", _("Toetswijze"))
    planfase = ChoiceItem("planfase", _("Planfase"))
    upload = ChoiceItem("upload", _("Upload"))
    meeting = ChoiceItem(
        "meeting",
        _("Vergadering"),
        show_unless=lambda project, current_step: project
        and project.toetswijze == Toetswijzen.versneld,  # noqa
    )
    confirmation = ChoiceItem(
        "confirmation",
        _("Bevestiging"),
        show_unless=lambda project, current_step: current_step != "confirmation",
        icon="check",
    )
