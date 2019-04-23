from django.views.generic import TemplateView, FormView

from .forms import ProjectGetOrCreateForm


class InfoPageView(TemplateView):
    template_name = "aanmeldformulier/info.html"


class SpecifyProjectView(FormView):
    form_class = ProjectGetOrCreateForm
    template_name = "aanmeldformulier/specify_project.html"

    def form_valid(self, form):
        pass
