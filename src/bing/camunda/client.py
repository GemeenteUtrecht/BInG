from urllib.parse import urljoin

import requests

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
        response = requests.request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response.json()
