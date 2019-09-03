import time
from dataclasses import dataclass
from typing import Any, Dict, List, Union

from zds_client import Client

from bing.cache.models import CachedResource

from .rewrites import URLRewriteMixin

Resource = Dict[str, Any]


@dataclass
class ClientWrapper(URLRewriteMixin, Client):
    """
    Wrap the client object and intercept all calls to rewrite URLs.
    """

    client: Client

    def __getattr__(self, attr: str):
        """
        Proxy to the underlying client.
        """
        return getattr(self.client, attr)

    def request(self, url: str, operation: str, method="GET", *args, **kwargs):
        """
        Intercept requests and response to rewrite URLs.
        """
        json = kwargs.get("json")
        if json:
            self.rewrite_urls(json)

        params = kwargs.get("params")
        if params:
            self.rewrite_urls(params)

        response = self._cached_request(url, operation, method=method, *args, **kwargs)

        if isinstance(response, (dict, list)):
            self.rewrite_urls(response, reverse=True)
        return response

    def _cached_request(self, url: str, operation: str, method="GET", *args, **kwargs):
        """
        Cache READ operation results, and return results from the cache.
        """
        should_cache = method == "GET"
        cached_response = None

        if should_cache:  # only read operations may be cached!
            cached_response = self._get_from_cache(url)
            if cached_response is not None:
                # TODO: log entry as cached
                return cached_response

        start = time.time()
        response = self.client.request(url, operation, method=method, *args, **kwargs)
        duration = time.time() - start
        self.client._log._entries[-1]["duration"] = int(duration * 1000)  # in ms

        if should_cache:
            self._cache(response)

        return response

    def _get_from_cache(self, url: str) -> Union[None, Resource]:
        rewrites = self._get_rewrites()
        url = self._rewrite_url(url, rewrites)
        cached = CachedResource.objects.filter(url=url).first()
        if cached is None:
            return None
        return cached.resource

    def _cache(self, response: Union[List[Resource], Resource]) -> None:
        if "results" in response:
            response = response["results"]

        if isinstance(response, dict):
            # TODO: only create what doesn't exist yet
            response = [response]

        existing_urls = CachedResource.objects.filter(
            url__in=[obj["url"] for obj in response]
        ).values_list("url", flat=True)
        response = [obj for obj in response if obj["url"] not in existing_urls]

        objs = [CachedResource(url=obj["url"], resource=obj) for obj in response]
        CachedResource.objects.bulk_create(objs)
