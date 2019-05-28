from django import forms
from django.db import transaction

from bing.meetings.models import Meeting


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("start", "end")

    @transaction.atomic
    def save(self, commit=True, *args, **kwargs):
        meeting = super().save(commit=commit, *args, **kwargs)
        if commit:
            meeting.ensure_zaak()
        return meeting
