from django import forms
from django.utils.translation import ugettext_lazy as _

from bing.projects.models import Project


class ProjectGetOrCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("project_id", "name")
        labels = {"project_id": _("Project-ID"), "name": _("Projectnaam")}

    def save(self, *args, **kwargs):
        # look up the project if it already exists
        project = Project.objects.filter(
            project_id=self.cleaned_data["project_id"]
        ).first()
        if project is not None:
            return project

        return super().save(*args, **kwargs)


class ProjectToetswijzeForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("toetswijze",)
        labels = {"toetswijze": _("Voor welke wijze van toetsen doet u het verzoek?")}
