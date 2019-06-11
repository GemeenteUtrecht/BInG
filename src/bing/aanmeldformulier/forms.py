import base64
import logging
import os

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from zds_client import ClientError

from bing.config.models import BInGConfig, RequiredDocuments
from bing.config.service import get_drc_client, get_zrc_client
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.models import Project, ProjectAttachment
from bing.service.ztc import get_aanvraag_iot

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
        config = BInGConfig.get_solo()

        io_type = self.cleaned_data["io_type"]
        content = self.cleaned_data["attachment"].read()
        filename = self.cleaned_data["attachment"].name

        # create informatieobject
        drc_client = get_drc_client(scopes=["zds.scopes.documenten.aanmaken"])
        eio = drc_client.create(
            "enkelvoudiginformatieobject",
            {
                "bronorganisatie": config.organisatie_rsin,
                "informatieobjecttype": io_type,
                "creatiedatum": timezone.now().date().isoformat(),
                "bestandsnaam": filename,
                "titel": os.path.splitext(filename)[0],
                "auteur": "BInG formulier",
                "taal": "dut",
                "inhoud": base64.b64encode(content).decode("ascii"),
            },
        )

        self.instance.io_type = io_type
        self.instance.eio_url = eio["url"]

        # connect io and zaak
        try:
            drc_client.create(
                "objectinformatieobject",
                {
                    "informatieobject": eio["url"],
                    "object": self.instance.project.zaak,
                    "objectType": "zaak",
                    "beschrijving": "Aangeleverd stuk door aanvrager",
                },
            )
        except ClientError as exc:
            logger.info("Trying new setup, got %s", exc)
            # try the new setup, with reversal of relation direction
            zrc_client = get_zrc_client()
            zrc_client.create(
                "zaakinformatieobject",
                {
                    "zaak": self.instance.project.zaak,
                    "informatieobject": eio["url"],
                    "beschrijving": "Aangeleverd stuk door aanvrager",
                },
            )

        return super().save(*args, **kwargs)


class ProjectAttachmentFormSet(forms.BaseModelFormSet):
    def __init__(self, project: Project, *args, **kwargs):
        kwargs["form_kwargs"] = {"project": project}
        super().__init__(*args, **kwargs)
