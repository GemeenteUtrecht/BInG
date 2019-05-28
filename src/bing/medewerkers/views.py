from django.views.generic import TemplateView

from .utils import fetch_vergadering_zaken, get_next_meeting


class IndexView(TemplateView):
    template_name = "medewerkers/index.html"


class KalenderView(TemplateView):
    """
    View to list (upcoming) BiNG sessions.
    """

    template_name = "medewerkers/kalender.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["next_meeting"] = get_next_meeting()
        context["object_list"] = fetch_vergadering_zaken()
        return context
