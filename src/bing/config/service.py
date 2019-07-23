from functools import partial
from urllib.parse import urljoin

import requests

from .client import ClientWrapper
from .models import APIConfig


def get_client(type: str, **claims) -> ClientWrapper:
    config = APIConfig.get_solo()
    service = getattr(config, type, None)
    if service is None:
        raise ValueError(f"No {type.upper()} configured!")

    client = service.build_client()
    wrapper = ClientWrapper(client)
    client.auth.user_id = "bing-user"
    client.auth.user_representation = "BInG Gebruiker"

    if claims:
        wrapper.rewrite_urls(claims)
        client.auth.set_claims(**claims)

    return wrapper


get_zrc_client = partial(get_client, "zrc")
get_ztc_client = partial(get_client, "ztc", scopes=["zds.scopes.zaaktypes.lezen"])
get_drc_client = partial(get_client, "drc")
get_brc_client = partial(get_client, "brc")


class Camunda:
    def __init__(self, config: APIConfig = None, path: str = "engine-rest/"):
        assert path.endswith("/"), "path must end with a trailing slash"
        config = config or APIConfig.get_solo()
        self._root = config.camunda_root
        self._path = path

    @property
    def root_url(self):
        return urljoin(self._root, self._path)

    def request(self, path: str, method="GET", *args, **kwargs):
        url = urljoin(self.root_url, path)
        response = requests.request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response.json()
