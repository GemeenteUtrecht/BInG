import copy
import logging
import time
from typing import Dict, List, Union
from urllib.parse import urljoin

import inflection
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

logger = logging.getLogger(__name__)


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
            if response.content:
                response_json = response.json()
            return underscoreize(response_json)
        except Exception:
            try:
                # see if we can grab any extra output
                response_json = response.json()
            except Exception:
                pass
            logger.exception("Error: %r", response_json)
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


def underscoreize(data: Union[List, Dict, str, None]) -> Union[List, Dict, str, None]:
    if isinstance(data, list):
        return [underscoreize(item) for item in data]

    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = inflection.underscore(key)
            new_data[new_key] = underscoreize(value)
        return new_data

    return data
