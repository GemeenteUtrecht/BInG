from django import forms
from django.utils.translation import ugettext_lazy as _

from bing.projects.models import Project


class ProjectGetOrCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("project_id", "name")
        labels = {"project_id": _("Project-ID"), "name": _("Projectnaam")}
