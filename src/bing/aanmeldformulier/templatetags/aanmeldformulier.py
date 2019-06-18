from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.template import Library

from bing.projects.models import Project

from ..constants import Steps

register = Library()


@dataclass
class Step:
    label: str
    active: bool
    icon: str = ""


@register.inclusion_tag("aanmeldformulier/includes/steps.html")
def form_steps(current_step: str, project: Optional[Project] = None) -> Dict[str, Any]:
    steps = []

    for step, label in Steps.choices:
        choice_item = Steps.get_choice(step)

        _step = Step(
            label=label,
            active=step == current_step,
            icon=getattr(choice_item, "icon", ""),
        )

        if hasattr(choice_item, "show_unless"):
            hide = choice_item.show_unless(project, current_step)
            if hide:
                continue

        steps.append(_step)

    context = {"steps": steps}

    return context
