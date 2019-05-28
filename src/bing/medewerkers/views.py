from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import MeetingForm
from .utils import fetch_vergadering_zaken, get_next_meeting


class IndexView(TemplateView):
    template_name = "medewerkers/index.html"


class KalenderView(CreateView):
    """
    View to list (upcoming) BiNG sessions.
    """

    form_class = MeetingForm
    template_name = "medewerkers/kalender.html"
    success_url = reverse_lazy("medewerkers:kalender")

    def get_initial(self):
        start, end = get_next_meeting()
        return {"start": start, "end": end}

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["object_list"] = fetch_vergadering_zaken()
        return context
