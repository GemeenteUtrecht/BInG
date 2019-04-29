import uuid
from urllib.parse import urljoin

from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel
from zds_client import Client, ClientAuth


def get_client(api_root: str) -> Client:
    dummy_resource = f"dummy/{uuid.uuid4()}"
    full_url = urljoin(api_root, dummy_resource)
    return Client.from_url(full_url)


class APIConfig(SingletonModel):
    drc_api_root = models.URLField(
        _("API root"), default="https://ref.tst.vng.cloud/drc/api/v1/"
    )
    drc_client_id = models.CharField(_("client id"), max_length=100, blank=True)
    drc_secret = models.CharField(_("secret"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("APIs configuration")

    def __str__(self):
        return force_text(self._meta.verbose_name)

    def get_drc_client(self) -> Client:
        client = get_client(self.drc_api_root)
        client.auth = ClientAuth(client_id=self.drc_client_id, secret=self.drc_secret)
        return client
