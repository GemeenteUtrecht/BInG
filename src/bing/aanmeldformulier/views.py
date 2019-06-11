from django.db import transaction
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView

from extra_views import ModelFormSetView

from bing.projects.models import Project, ProjectAttachment

from .constants import PROJECT_SESSION_KEY
from .decorators import project_required
from .forms import (
    ProjectAttachmentForm,
    ProjectAttachmentFormSet,
    ProjectGetOrCreateForm,
    ProjectPlanfaseForm,
    ProjectToetswijzeForm,
)


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
    success_url = reverse_lazy("aanmeldformulier:planfase")

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)


@method_decorator(project_required, name="dispatch")
class PlanfaseView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectPlanfaseForm
    template_name = "aanmeldformulier/planfase.html"
    success_url = reverse_lazy("aanmeldformulier:upload")

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
    success_url = reverse_lazy("aanmeldformulier:info")

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["attachments"] = project.get_documents()
        return context
