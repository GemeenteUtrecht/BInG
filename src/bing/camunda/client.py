import copy
import time
from typing import Dict
from urllib.parse import urljoin

import requests
from zds_client.client import Client

from bing.config.models import APIConfig, BInGConfig
from bing.config.service import (
    get_brc_client,
    get_drc_client,
    get_nrc_client,
    get_zrc_client,
    get_ztc_client,
)


def get_api_token_headers() -> Dict[str, str]:
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(
        scopes=[
            "zds.scopes.zaken.lezen",
            "zds.scopes.zaken.aanmaken",
            "zds.scopes.zaken.bijwerken",
        ],
        zaaktypes=[config.zaaktype_aanvraag, config.zaaktype_vergadering],
    )
    drc_client = get_drc_client()
    ztc_client = get_ztc_client()
    brc_client = get_brc_client()
    nrc_client = get_nrc_client(scopes=["notificaties.scopes.publiceren"])

    return {
        "Token-ZRC": zrc_client.client.auth.credentials()["Authorization"],
        "Token-DRC": drc_client.client.auth.credentials()["Authorization"],
        "Token-ZTC": ztc_client.client.auth.credentials()["Authorization"],
        "Token-BRC": brc_client.client.auth.credentials()["Authorization"],
        "Token-NRC": nrc_client.client.auth.credentials()["Authorization"],
    }


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

        # add the API headers, so that Camunda can use the tokens. Essentially
        # we're forwarding Auth
        headers = kwargs.pop("headers", {})
        headers.update(get_api_token_headers())
        kwargs["headers"] = headers

        start = time.time()
        response = requests.request(method, url, *args, **kwargs)
        response_json = None

        try:
            response.raise_for_status()
            response_json = response.json()
            return response_json
        except Exception:
            raise
        finally:
            duration = time.time() - start
            Client._log.add(
                "camunda",
                url,
                method,
                kwargs.get("headers") or {},
                copy.deepcopy(kwargs.get("data", kwargs.get("json", None))),
                response.status_code,
                dict(response.headers),
                response_json,
            )
            Client._log._entries[-1]["duration"] = int(duration * 1000)  # in ms
