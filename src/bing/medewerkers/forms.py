from django import forms
from django.db import transaction
from django.template.defaultfilters import date

from bing.meetings.models import Meeting
from bing.meetings.tasks import add_project_to_meeting, ensure_meeting_zaak
from bing.projects.constants import Toetswijzen, PlanFases
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
        project = super().save(commit=commit, *args, **kwargs)

        meeting = self.cleaned_data["meeting"]
        if commit and meeting:
            transaction.on_commit(
                lambda: add_project_to_meeting.delay(meeting.id, self.instance.id)
            )

        return project
