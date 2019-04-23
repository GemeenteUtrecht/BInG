from django.db import transaction
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView

from bing.projects.models import Project

from .constants import PROJECT_SESSION_KEY
from .decorators import project_required
from .forms import ProjectGetOrCreateForm, ProjectToetswijzeForm


class ProjectMixin:
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

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
    success_url = reverse_lazy("aanmeldformulier:info")
