import logging
import os

from django import forms
from django.conf import settings
from django.core.files import temp as tempfile
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bing.config.models import BInGConfig, RequiredDocuments
from bing.meetings.models import Meeting
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.models import Project, ProjectAttachment
from bing.service.ztc import get_aanvraag_iot

from .tasks import add_project_attachment

logger = logging.getLogger(__name__)


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

        # FIXME: should only happen after final submission!
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


class ProjectPlanfaseForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("planfase",)
        labels = {"planfase": _("Voor welke planfase dient getoetst te worden?")}
        widgets = {"planfase": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["planfase"].choices = PlanFases.choices


class ProjectAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(label=_("bestand"), required=False)

    class Meta:
        model = ProjectAttachment
        fields = ("io_type",)
        widgets = {"io_type": forms.RadioSelect}

    def __init__(self, project: Project, *args, **kwargs):
        self.project = project

        super().__init__(*args, **kwargs)

        io_types = get_aanvraag_iot()

        try:
            io_types_config = RequiredDocuments.objects.get(
                toetswijze=project.toetswijze
            )
        except RequiredDocuments.DoesNotExist:
            logger.warning(
                "No RequiredDocuments for toetswijze '%s' configured",
                project.toetswijze,
            )
        else:
            io_types = [
                (io_type, label)
                for io_type, label in io_types
                if io_type in io_types_config.informatieobjecttypen
            ]

        self.fields["io_type"].choices = io_types

    def save(self, *args, **kwargs):
        self.instance.project = self.project

        attachment = super().save(*args, **kwargs)

        # create a temp file
        name = self.cleaned_data["attachment"].name
        _, ext = os.path.splitext(name)

        with tempfile.NamedTemporaryFile(
            suffix=".upload" + ext, dir=settings.FILE_UPLOAD_TEMP_DIR, delete=False
        ) as temp_file:
            temp_file.write(self.cleaned_data["attachment"].read())

        # handle the rest in Celery
        add_project_attachment.delay(attachment.id, name, temp_file.name)

        return attachment


class ProjectAttachmentFormSet(forms.BaseModelFormSet):
    def __init__(self, project: Project, *args, **kwargs):
        kwargs["form_kwargs"] = {"project": project}
        super().__init__(*args, **kwargs)


class MeetingField(forms.ModelChoiceField):
    widget = forms.RadioSelect

    def __init__(self, queryset, *args, **kwargs):
        kwargs.setdefault("empty_label", _("Geen voorkeur"))
        kwargs["help_text"] = ""

        config = BInGConfig.get_solo()
        earliest_start = (timezone.now() + config.minimal_plan_duration).replace(
            hour=0, minute=0, second=0
        )
        queryset = queryset.filter(start__gt=earliest_start)

        super().__init__(queryset, *args, **kwargs)

    def label_from_instance(self, obj):
        return date(obj.start)


class ProjectMeetingForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("meeting",)
        field_classes = {"meeting": MeetingField}
        labels = {"meeting": _("Kies uw gewenste vergaderdatum")}
