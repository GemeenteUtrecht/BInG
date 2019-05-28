from django.db.models import Count, Max
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from bing.meetings.models import Meeting
from bing.projects.models import Project

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
        # determine last planned meeting from local objects...
        max_start = Meeting.objects.aggregate(Max("start"))["start__max"]
        start, end = get_next_meeting(after=max_start)
        return {"start": start, "end": end}

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["object_list"] = fetch_vergadering_zaken()
        return context


class ProjectsView(ListView):
    queryset = Project.objects.exclude(zaak="").annotate(num_meetings=Count("meeting"))
    template_name = "medewerkers/projects.html"
