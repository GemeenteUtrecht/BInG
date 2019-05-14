import base64
import os

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bing.config.models import APIConfig, BInGConfig
from bing.config.service import get_drc_client, get_ztc_client
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


class ProjectAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(label=_("bestand"), required=False)

    class Meta:
        model = ProjectAttachment
        fields = ("io_type",)
        widgets = {"io_type": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = BInGConfig.get_solo()
        api_config = APIConfig.get_solo()
        ztc_client = get_ztc_client()

        # fetch informatieobjecttypen efficiently
        zaaktype = ztc_client.retrieve("zaaktype", url=config.zaaktype_aanvraag)
        main_catalogus_uuid = api_config.ztc.extra["main_catalogus_uuid"]
        informatieobjecttypen = ztc_client.list(
            "informatieobjecttype", catalogus_uuid=main_catalogus_uuid
        )
        informatieobjecttypen = [
            iot
            for iot in informatieobjecttypen
            if iot["url"] in zaaktype["informatieobjecttypen"]
        ]

        iot_choices = [
            (iot["url"], iot["omschrijving"]) for iot in informatieobjecttypen
        ]

        self.fields["io_type"].choices = iot_choices

    def save(self, *args, **kwargs):
        config = BInGConfig.get_solo()

        io_type = self.cleaned_data["io_type"]
        content = self.cleaned_data["attachment"].read()
        filename = self.cleaned_data["attachment"].name

        # create informatieobject
        drc_client = get_drc_client(scopes=[])
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
        drc_client.create(
            "objectinformatieobject",
            {
                "informatieobject": eio["url"],
                "object": self.instance.project.zaak,
                "objectType": "zaak",
                "beschrijving": "Aangeleverd stuk door aanvrager",
            },
        )

        return super().save(*args, **kwargs)
