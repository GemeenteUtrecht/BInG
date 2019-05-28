from django import forms
from django.db import transaction

from bing.meetings.models import Meeting
from bing.meetings.tasks import ensure_meeting_zaak
from bing.projects.constants import Toetswijzen
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


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("toetswijze", "meeting")
        widgets = {"toetswijze": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["toetswijze"].choices = [
            (value, label)
            for value, label in Toetswijzen.choices
            if value != Toetswijzen.onbekend
        ]
