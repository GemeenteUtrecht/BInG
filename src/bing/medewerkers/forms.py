from django import forms
from django.db import transaction
from django.template.defaultfilters import date

from bing.meetings.models import Meeting
from bing.meetings.tasks import (
    add_project_to_meeting,
    ensure_meeting_zaak,
    remove_project_from_meeting,
)
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.models import Project


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

    @transaction.atomic
    def save(self, commit=True, *args, **kwargs):
        current_meeting = self.instance.meeting

        # notify toetswijze
        if self.instance.toetswijze != self.cleaned_data["toetswijze"]:
            msg = "De BInG secretaris heeft de toetswijze aangepast van {oud} naar {nieuw}".format(
                oud=self.instance.get_toetswijze_display(),
                nieuw=Toetswijzen.labels[self.cleaned_data["toetswijze"]],
            )
            transaction.on_commit(lambda: project.notify(msg))

        should_clear_meeting = self.cleaned_data["toetswijze"] == Toetswijzen.versneld

        # TODO: doorlooptijd zaak aanpassen
        if should_clear_meeting:
            self.cleaned_data["meeting"] = None

        project = super().save(commit=commit, *args, **kwargs)

        meeting = self.cleaned_data["meeting"]
        if not commit:
            return project

        if meeting:
            transaction.on_commit(
                lambda: add_project_to_meeting.delay(meeting.id, self.instance.id)
            )
        elif current_meeting and should_clear_meeting:
            transaction.on_commit(
                lambda: remove_project_from_meeting.delay(
                    current_meeting.id, self.instance.id
                )
            )

        return project
