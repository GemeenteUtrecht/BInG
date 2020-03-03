from mimetypes import guess_extension

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Max
from django.http import StreamingHttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import FormMixin

from bing.meetings.models import Meeting
from bing.projects.models import Project, ProjectAttachment

from .decorators import camunda_task
from .forms import (
    MeetingForm,
    MeetingStatusForm,
    ProjectBesluitForm,
    ProjectProcedureForm,
    ProjectStatusForm,
    ProjectUpdateForm,
)
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

        context["object_list"] = [
            (meetings[url], zaak) for url, zaak in zaken.items() if url in meetings
        ]
        return context


class StatusFormMixin(FormMixin):
    def get_initial(self) -> dict:
        initial = super().get_initial()

        # fetch current status information
        # FIXME fetch zaak, status and resultaat
        # zaak = fetch_zaak(self.object.zaak)
        # current_status_type = fetch_status(zaak["status"])["statusType"]
        # current_resultaat = fetch_resultaat(zaak["resultaat"])
        zaak = {}
        current_status_type = ""
        current_resultaat = {}
        current_resultaat_type = (
            current_resultaat["resultaatType"] if current_resultaat else ""
        )

        initial.update(
            {"status": current_status_type, "resultaat": current_resultaat_type}
        )
        return initial

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save(obj=self.object)
        return super().form_valid(form)


class MeetingDetailView(LoginRequiredMixin, StatusFormMixin, DetailView):
    """
    Display the information of a single meeting.
    """

    queryset = Meeting.objects.exclude(zaak="")
    form_class = MeetingStatusForm
    template_name = "medewerkers/meeting.html"
    context_object_name = "meeting"

    def get_success_url(self):
        return reverse("medewerkers:meeting-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FIXME add zaak, project_zaken
        # zaak = fetch_zaak(self.object.zaak)

        # context["zaak"] = zaak

        # project_zaken = {
        #     zaak["url"]: zaak for zaak in fetch_zaken(zaak["relevanteAndereZaken"])
        # }
        project_zaken = {}
        projects = {
            project.zaak: project
            for project in Project.objects.filter(zaak__in=project_zaken)
        }

        context["projects"] = [
            (projects[url], zaak)
            for url, zaak in project_zaken.items()
            if url in projects
        ]
        return context


class ProjectsView(LoginRequiredMixin, ListView):
    queryset = (
        Project.objects.exclude(zaak="").select_related("meeting").order_by("-pk")
    )
    template_name = "medewerkers/projects.html"


class ProjectDetailView(LoginRequiredMixin, StatusFormMixin, DetailView):
    """
    Display all the project information.
    """

    queryset = Project.objects.exclude(zaak="")
    form_class = ProjectStatusForm
    template_name = "medewerkers/project.html"
    context_object_name = "project"

    def get_success_url(self):
        return reverse("medewerkers:project-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        documents = self.object.get_documents()
        if documents:
            documents = sorted(documents, key=lambda doc: (doc.get("document_type")))
            context["documents"] = documents

        # FIXME add besluiten
        # context["besluiten"] = fetch_besluiten(zaak=self.object.zaak)

        return context


class ProjectBesluitCreate(LoginRequiredMixin, UpdateView):
    queryset = Project.objects.exclude(zaak="")
    form_class = ProjectBesluitForm
    template_name = "medewerkers/project_besluit.html"

    def get_success_url(self):
        return reverse("medewerkers:project-detail", kwargs={"pk": self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    queryset = Project.objects.exclude(zaak="")
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

        # document = fetch_document(url=attachment.eio_url)
        # FIXME add document
        document = {}
        content_type = document["formaat"] or "application/octet-stream"

        default = f"attachment{guess_extension(content_type)}"
        filename = document["bestandsnaam"] or default

        # FIXME add content
        content = document["inhoud"]
        response = StreamingHttpResponse(
            streaming_content=content, content_type=content_type
        )
        response["Content-Length"] = document["bestandsomvang"]
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class UserTasksView(LoginRequiredMixin, TemplateView):
    """
    Fetch and display the open user tasks in Camunda.
    """

    template_name = "medewerkers/tasks.html"

    def get_context_data(self, **kwargs) -> dict:
        # FIXME get tasks
        # kwargs["tasks"] = get_aanvraag_tasks()
        return super().get_context_data(**kwargs)


@camunda_task
class DetermineProcedureView(LoginRequiredMixin, UpdateView):
    queryset = (
        Project.objects
        # .exclude(zaak="")
        .exclude(camunda_process_instance_id="")
    )
    template_name = "medewerkers/determine_procedure.html"
    form_class = ProjectProcedureForm
    success_url = reverse_lazy("medewerkers:tasks")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # FIXME get task
        # kwargs["task"] = get_task(self.kwargs["task_id"])
        return kwargs
