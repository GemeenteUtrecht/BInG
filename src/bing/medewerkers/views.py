from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from bing.meetings.models import Meeting
from bing.projects.models import Project

from .forms import MeetingForm, ProjectUpdateForm
from .utils import fetch_vergadering_zaken, fetch_zaak, fetch_zaken, get_next_meeting


class LoginView(LoginView):
    template_name = "medewerkers/login.html"


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "medewerkers/index.html"


class KalenderView(LoginRequiredMixin, CreateView):
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
        zaken = {zaak["url"]: zaak for zaak in fetch_vergadering_zaken()}
        qs = Meeting.objects.filter(zaak__in=zaken)
        meetings = {meeting.zaak: meeting for meeting in qs}

        context["object_list"] = [(meetings[url], zaak) for url, zaak in zaken.items()]
        return context


class MeetingDetailView(LoginRequiredMixin, DetailView):
    queryset = Meeting.objects.exclude(zaak="")
    template_name = "medewerkers/meeting.html"
    context_object_name = "meeting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaak = fetch_zaak(self.object.zaak)
        context["zaak"] = zaak
        context["projects"] = fetch_zaken(zaak["relevanteAndereZaken"])
        return context


class ProjectsView(LoginRequiredMixin, ListView):
    queryset = Project.objects.exclude(zaak="").order_by("-pk")
    template_name = "medewerkers/projects.html"


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    queryset = Project.objects.exclude(zaak="").annotate(num_meetings=Count("meeting"))
    template_name = "medewerkers/project_form.html"
    form_class = ProjectUpdateForm
    success_url = reverse_lazy("medewerkers:kalender")
