from django import forms

from bing.meetings.models import Meeting


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ("start", "end")
