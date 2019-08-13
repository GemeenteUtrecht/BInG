import copy
import time
from urllib.parse import urljoin

import requests
from zds_client.client import Client

from bing.config.models import APIConfig


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
