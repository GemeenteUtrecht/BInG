from io import StringIO

from django import forms
from django.utils.translation import ugettext_lazy as _

from .client import Camunda
from .models import Deployment


class DeploymentForm(forms.ModelForm):
    xml = forms.CharField(
        label=_("Process definition XML"),
        widget=forms.Textarea,
        help_text=_("XML content of the process model"),
    )

    class Meta:
        model = Deployment
        fields = "__all__"

    def update_in_camunda(self, deployment: Deployment):
        client = Camunda()
        client.request(
            "deployment/create",
            method="POST",
            data={
                "deployment-name": deployment.name,
                "enable-duplicate-filtering": "true",
                "deploy-changed-only": "true",
                "deployment-source": "bing",
            },
            files={"definition.bpmn": StringIO(self.cleaned_data["xml"])},
        )
