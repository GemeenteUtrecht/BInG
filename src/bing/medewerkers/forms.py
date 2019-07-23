import os
import tempfile
from typing import Callable

from django import forms
from django.conf import settings
from django.db import models, transaction
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bing.config.models import RequiredDocuments
from bing.meetings.models import Meeting
from bing.meetings.tasks import (
    add_project_to_meeting,
    ensure_meeting_zaak,
    remove_project_from_meeting,
)
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.models import Project
from bing.service.ztc import (
    get_aanvraag_besluittypen,
    get_aanvraag_iot,
    get_aanvraag_resultaattypen,
    get_aanvraag_statustypen,
    get_vergadering_resultaattypen,
    get_vergadering_statustypen,
)

from .tasks import add_besluit, set_new_status, set_result


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("start", "end")

    @transaction.atomic
    def save(self, commit=True, *args, **kwargs):
        meeting = super().save(commit=commit, *args, **kwargs)
        if commit:
            transaction.on_commit(lambda: ensure_meeting_zaak.delay(meeting.id))
        return meeting


class MeetingField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return date(obj.start)


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("toetswijze", "planfase", "meeting")
        widgets = {"toetswijze": forms.RadioSelect, "planfase": forms.RadioSelect}
        field_classes = {"meeting": MeetingField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["toetswijze"].choices = [
            (value, label)
            for value, label in Toetswijzen.choices
            if value != Toetswijzen.onbekend
        ]
        self.fields["planfase"].choices = [
            (value, label)
            for value, label in PlanFases.choices
            if value != PlanFases.onbekend
        ]

        self.fields["meeting"].queryset = self.fields["meeting"].queryset.filter(
            start__gte=timezone.now()
        )

    @transaction.atomic
    def save(self, commit=True, *args, **kwargs):
        project = Project.objects.select_related("meeting").get(pk=self.instance.pk)
        current_meeting = project.meeting

        toetswijze_changed = project.toetswijze != self.cleaned_data["toetswijze"]

        # notify toetswijze
        if commit and toetswijze_changed:
            msg = "De BInG secretaris heeft de toetswijze aangepast van {oud} naar {nieuw}".format(
                oud=project.get_toetswijze_display(),
                nieuw=Toetswijzen.labels[self.cleaned_data["toetswijze"]],
            )
            transaction.on_commit(lambda: project.notify(msg))

        should_clear_meeting = self.cleaned_data["toetswijze"] == Toetswijzen.versneld

        # TODO: doorlooptijd zaak aanpassen
        if should_clear_meeting:
            self.cleaned_data["meeting"] = None

        if (
            commit
            and toetswijze_changed
            and self.cleaned_data["toetswijze"] == Toetswijzen.regulier
        ):
            # check for missing documents
            io_types = project.projectattachment_set.values_list(
                "io_type", flat=True
            ).distinct()
            io_types_config = RequiredDocuments.objects.get(
                toetswijze=Toetswijzen.regulier
            )
            missing = set(io_types_config.informatieobjecttypen) - set(io_types)
            if missing:
                io_types = get_aanvraag_iot()
                document_types = [label for url, label in io_types if url in missing]
                msg = (
                    "De toetswijze is gewijzigd naar '{toetswijze}'. Hierdoor dient u "
                    "ook nog de volgende documenttypen aan te leveren: {document_types}"
                ).format(
                    toetswijze=Toetswijzen.labels[Toetswijzen.regulier],
                    document_types=", ".join(sorted(document_types)),
                )
                transaction.on_commit(lambda: project.notify(msg))

        project = super().save(commit=commit, *args, **kwargs)

        meeting = self.cleaned_data["meeting"]
        if not commit:
            return project

        if meeting:
            transaction.on_commit(
                lambda: add_project_to_meeting.delay(meeting.id, project.id)
            )
        elif current_meeting and should_clear_meeting:
            transaction.on_commit(
                lambda: remove_project_from_meeting.delay(
                    current_meeting.id, project.id
                )
            )
        elif meeting and current_meeting != meeting:

            def change_meeting():
                remove_project_from_meeting.delay(current_meeting.id, project.id)
                add_project_to_meeting.delay(meeting.id, project.id)

            transaction.on_commit(change_meeting)

        return project


class StatusForm(forms.Form):
    status = forms.ChoiceField(label=_("Status"), choices=())
    resultaat = forms.ChoiceField(
        label=_("Resultaat"),
        choices=(),
        required=False,
        help_text=_(
            "Ken een resultaat toe. Een resultaat is verplicht vóór het afsluiten van de zaak."
        ),
    )

    GET_STATUSTYPEN: Callable = None
    GET_RESULTAATTYPEN: Callable = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = self.GET_STATUSTYPEN()
        self.fields["resultaat"].choices = [("", "-------")] + self.GET_RESULTAATTYPEN()

    def clean(self):
        super().clean()

        last_choice = self.fields["status"].choices[-1][0]
        status = self.cleaned_data.get("status")
        resultaat = self.cleaned_data.get("resultaat")

        if status == last_choice:
            if not resultaat:
                self.add_error(
                    "status",
                    _("You cannot set the final status unless a result has been set."),
                )

    def save(self, obj: models.Model):
        """
        Persist the changes in the ZRC.

        TODO: if the last status is being set and the result at the same time,
        then the status-set should be chained AFTER completion of the result
        setting.
        """

        # set the new status, if it has changed
        old_status = self.initial.get("status")
        new_status = self.cleaned_data["status"]
        if new_status != old_status:
            set_new_status.delay(obj.zaak, new_status)

        # set the result, if it has changed
        old_resultaat = self.initial.get("resultaat")
        new_resultaat = self.cleaned_data["resultaat"]
        if new_resultaat != old_resultaat:
            set_result.delay(obj.zaak, new_resultaat)


class ProjectStatusForm(StatusForm):
    GET_STATUSTYPEN = staticmethod(get_aanvraag_statustypen)
    GET_RESULTAATTYPEN = staticmethod(get_aanvraag_resultaattypen)


class MeetingStatusForm(StatusForm):
    GET_STATUSTYPEN = staticmethod(get_vergadering_statustypen)
    GET_RESULTAATTYPEN = staticmethod(get_vergadering_resultaattypen)


class ProjectBesluitForm(forms.ModelForm):
    besluittype = forms.ChoiceField(
        label=_("soort besluit"), choices=(), widget=forms.RadioSelect
    )
    start_date = forms.DateField(label=_("Ingangsdatum"))
    end_date = forms.DateField(label=_("Vervaldatum"), required=False)
    final_reaction_date = forms.DateField(
        label=_("Uiterlijke reactiedatum"), required=False
    )
    attachment = forms.FileField(
        label=_("bestand"), help_text=_("Document waarin het besluit is vastgelegd.")
    )

    class Meta:
        model = Project
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["besluittype"].choices = get_aanvraag_besluittypen()

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)

        # create a temp file
        name = self.cleaned_data["attachment"].name
        _, ext = os.path.splitext(name)

        with tempfile.NamedTemporaryFile(
            suffix=".upload" + ext, dir=settings.FILE_UPLOAD_TEMP_DIR, delete=False
        ) as temp_file:
            temp_file.write(self.cleaned_data["attachment"].read())

        end_date = self.cleaned_data.get("end_date")
        final_reaction_date = self.cleaned_data.get("final_reaction_date")
        besluit_data = {
            "besluittype": self.cleaned_data["besluittype"],
            "ingangsdatum": self.cleaned_data["start_date"].isoformat(),
            "vervaldatum": end_date.isoformat() if end_date else None,
            "uiterlijkeReactiedatum": final_reaction_date.isoformat()
            if final_reaction_date
            else None,
        }

        add_besluit.delay(self.instance.pk, name, temp_file.name, **besluit_data)

        return obj
