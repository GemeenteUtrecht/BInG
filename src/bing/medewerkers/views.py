from mimetypes import guess_extension

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max
from django.http import StreamingHttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import BaseDetailView

from bing.meetings.models import Meeting
from bing.projects.models import Project, ProjectAttachment
from bing.service.drc import fetch_document, stream_inhoud
from bing.service.zrc import fetch_zaak, fetch_zaken

from .forms import MeetingForm, ProjectUpdateForm
from .utils import fetch_vergadering_zaken, get_next_meeting


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
    """
    Display the information of a single meeting.
    """

    queryset = Meeting.objects.exclude(zaak="")
    template_name = "medewerkers/meeting.html"
    context_object_name = "meeting"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaak = fetch_zaak(self.object.zaak)
        context["zaak"] = zaak

        project_zaken = {
            zaak["url"]: zaak for zaak in fetch_zaken(zaak["relevanteAndereZaken"])
        }
        projects = {
            project.zaak: project
            for project in Project.objects.filter(zaak__in=project_zaken)
        }

        context["projects"] = [
            (projects[url], zaak) for url, zaak in project_zaken.items()
        ]
        return context


class ProjectsView(LoginRequiredMixin, ListView):
    queryset = (
        Project.objects.exclude(zaak="").select_related("meeting").order_by("-pk")
    )
    template_name = "medewerkers/projects.html"


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """
    Display all the project information.
    """

    queryset = Project.objects.exclude(zaak="")
    template_name = "medewerkers/project.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        documents = self.object.get_documents()
        documents = sorted(documents, key=lambda doc: (doc["document_type"]))
        context["documents"] = documents
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    queryset = Project.objects.exclude(zaak="").annotate(num_meetings=Count("meeting"))
    template_name = "medewerkers/project_form.html"
    form_class = ProjectUpdateForm
    success_url = reverse_lazy("medewerkers:kalender")


class AttachmentDownloadView(LoginRequiredMixin, BaseDetailView):
    queryset = (
        ProjectAttachment.objects.exclude(project__zaak="")
        .exclude(io_type="")
        .exclude(eio_url="")
    )

    def get(self, request, *args, **kwargs):
        attachment = self.get_object()

        document = fetch_document(url=attachment.eio_url)
        content_type = document["formaat"] or "application/octet-stream"

        default = f"attachment{guess_extension(content_type)}"
        filename = document["bestandsnaam"] or default

        content = stream_inhoud(document["inhoud"])
        response = StreamingHttpResponse(
            streaming_content=content, content_type=content_type
        )
        response["Content-Length"] = document["bestandsomvang"]
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
