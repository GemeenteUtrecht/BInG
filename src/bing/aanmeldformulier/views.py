import base64
import os

from django.db import transaction
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from bing.config.models import RSIN
from bing.config.service import get_drc_client
from bing.projects.models import Project

from .constants import PROJECT_SESSION_KEY
from .decorators import project_required
from .forms import ProjectAttachmentForm, ProjectGetOrCreateForm, ProjectToetswijzeForm


class ProjectMixin:
    def get_project(self, queryset=None):
        if queryset is None:
            queryset = Project.objects.all()

        project_id = self.request.session[PROJECT_SESSION_KEY]
        return queryset.get(id=project_id)


class InfoPageView(TemplateView):
    template_name = "aanmeldformulier/info.html"


class SpecifyProjectView(FormView):
    form_class = ProjectGetOrCreateForm
    template_name = "aanmeldformulier/specify_project.html"
    success_url = reverse_lazy("aanmeldformulier:toetswijze")

    @transaction.atomic()
    def form_valid(self, form):
        project = form.save()
        self.request.session[PROJECT_SESSION_KEY] = project.id
        return super().form_valid(form)


@method_decorator(project_required, name="dispatch")
class ToetswijzeView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectToetswijzeForm
    template_name = "aanmeldformulier/toetswijze.html"
    success_url = reverse_lazy("aanmeldformulier:upload")

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)


@method_decorator(project_required, name="dispatch")
class UploadView(ProjectMixin, CreateView):
    form_class = ProjectAttachmentForm
    template_name = "aanmeldformulier/upload.html"
    success_url = reverse_lazy("aanmeldformulier:info")

    @transaction.atomic()
    def form_valid(self, form):
        form.instance.project = self.get_project()

        io_type = form.cleaned_data["io_type"]
        content = form.cleaned_data["attachment"].read()
        filename = form.cleaned_data["attachment"].name

        client = get_drc_client(scopes=[])
        eio = client.create(
            "enkelvoudiginformatieobject",
            {
                "bronorganisatie": RSIN,
                "informatieobjecttype": io_type,
                "creatiedatum": timezone.now().date().isoformat(),
                "bestandsnaam": filename,
                "titel": os.path.splitext(filename)[0],
                "auteur": "BInG formulier",
                "taal": "dut",
                "inhoud": base64.b64encode(content).decode("ascii"),
            },
        )

        form.instance.io_type = io_type
        form.instance.eio_url = eio["url"]

        return super().form_valid(form)
