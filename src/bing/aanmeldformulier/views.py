from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView

from extra_views import ModelFormSetView

from bing.config.models import RequiredDocuments
from bing.projects.constants import Toetswijzen
from bing.projects.models import Project, ProjectAttachment
from bing.service.zrc import fetch_zaak
from bing.service.ztc import get_aanvraag_iot

from .constants import PROJECT_SESSION_KEY, Steps
from .decorators import project_required
from .forms import (
    ProjectAttachmentForm,
    ProjectAttachmentFormSet,
    ProjectGetOrCreateForm,
    ProjectMeetingForm,
    ProjectPlanfaseForm,
    ProjectToetswijzeForm,
)


class ProjectMixin:
    def get_project(self, queryset=None):
        if queryset is None:
            queryset = Project.objects.all()

        project_id = self.request.session[PROJECT_SESSION_KEY]
        return queryset.get(id=project_id)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("project", self.get_project())
        return super().get_context_data(**kwargs)


class InfoPageView(TemplateView):
    template_name = "aanmeldformulier/info.html"


class SpecifyProjectView(FormView):
    form_class = ProjectGetOrCreateForm
    template_name = "aanmeldformulier/specify_project.html"
    success_url = reverse_lazy("aanmeldformulier:toetswijze")
    current_step = Steps.info

    def get_initial(self):
        initial = super().get_initial()
        project_pk = self.request.session.get(PROJECT_SESSION_KEY)
        if project_pk:
            project = Project.objects.filter(pk=project_pk).first()
            if project:
                initial["project_id"] = project.project_id
        return initial

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
    success_url = reverse_lazy("aanmeldformulier:planfase")
    current_step = Steps.toetswijze

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)


@method_decorator(project_required, name="dispatch")
class PlanfaseView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectPlanfaseForm
    template_name = "aanmeldformulier/planfase.html"
    success_url = reverse_lazy("aanmeldformulier:upload")
    current_step = Steps.planfase

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)


@method_decorator(project_required, name="dispatch")
class UploadView(ProjectMixin, ModelFormSetView):
    model = ProjectAttachment
    queryset = ProjectAttachment.objects.none()
    form_class = ProjectAttachmentForm
    formset_class = ProjectAttachmentFormSet
    factory_kwargs = {"extra": 3}
    template_name = "aanmeldformulier/upload.html"
    success_url = reverse_lazy("aanmeldformulier:vergadering")
    current_step = Steps.upload

    # TODO: Simple cache....
    _req_doc_types = []

    def get_required_document_types(self):
        if not self._req_doc_types:
            required_io_types = []
            io_types = get_aanvraag_iot()

            try:
                io_types_config = RequiredDocuments.objects.get(
                    toetswijze=self.get_project().toetswijze
                )
            except RequiredDocuments.DoesNotExist:
                logger.warning(
                    "No RequiredDocuments for toetswijze '%s' configured",
                    project.toetswijze,
                )
            else:
                required_io_types = [
                    (io_type, label)
                    for io_type, label in io_types
                    if io_type in io_types_config.informatieobjecttypen
                ]
                self._req_doc_types = required_io_types
        return self._req_doc_types


    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["project"] = self.get_project()

        kwargs["initial"] = [{'io_type': doc_type[0]} for doc_type in self.get_required_document_types()]
        print(kwargs['initial'])
        return kwargs

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs['extra'] = len(self.get_required_document_types())
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["attachments"] = project.get_documents()
        return context


@method_decorator(project_required, name="dispatch")
class MeetingView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectMeetingForm
    template_name = "aanmeldformulier/meeting.html"
    success_url = reverse_lazy("aanmeldformulier:confirmation")
    current_step = Steps.meeting

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)

    def get(self, request, *args, **kwargs):
        self.object = project = self.get_project()

        # shortcut - this step isn't needed
        if project.toetswijze == Toetswijzen.versneld:
            return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)


@method_decorator(project_required, name="dispatch")
class ConfirmationView(ProjectMixin, TemplateView):
    template_name = "aanmeldformulier/confirmation.html"
    current_step = Steps.confirmation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        zaak = fetch_zaak(self.get_project().zaak)
        context["identificatie"] = zaak["identificatie"]
        return context
