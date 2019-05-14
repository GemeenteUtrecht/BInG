from django import forms
from django.utils.translation import ugettext_lazy as _

from bing.projects.constants import Toetswijzen
from bing.projects.models import Project, ProjectAttachment


class ProjectGetOrCreateForm(forms.ModelForm):
    project_id = forms.CharField(
        label=_("Project-ID"),
        max_length=Project._meta.get_field("project_id").max_length,
    )

    class Meta:
        model = Project
        fields = ("name",)
        labels = {"name": _("Projectnaam")}

    def save(self, *args, **kwargs):
        # look up the project if it already exists
        project = Project.objects.filter(
            project_id=self.cleaned_data["project_id"]
        ).first()
        if project is None:
            self.instance.project_id = self.cleaned_data["project_id"]
            project = super().save(*args, **kwargs)

        project.ensure_zaak()

        return project


class ProjectToetswijzeForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("toetswijze",)
        labels = {"toetswijze": _("Voor welke wijze van toetsen doet u het verzoek?")}
        widgets = {"toetswijze": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["toetswijze"].choices = Toetswijzen.choices


class ProjectAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(label=_("bestand"), required=False)

    class Meta:
        model = ProjectAttachment
        fields = ("io_type",)
