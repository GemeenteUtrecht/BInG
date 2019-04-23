from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import ProjectGetOrCreateForm


class InfoPageView(TemplateView):
    template_name = "aanmeldformulier/info.html"


class SpecifyProjectView(FormView):
    form_class = ProjectGetOrCreateForm
    template_name = "aanmeldformulier/specify_project.html"
    success_url = reverse_lazy("aanmeldformulier:info")

    @transaction.atomic()
    def form_valid(self, form):
        project = form.save()
        self.session['project_id'] = project.id
        return super().form_valid(form)
