import logging
from typing import Any, Dict, Iterator

import requests

from bing.config.service import get_drc_client

logger = logging.getLogger(__name__)


def fetch_document(url: str) -> Dict[str, Any]:
    """
    Retrieve a single Document by URL.
    """
    drc_client = get_drc_client(scopes=["zds.scopes.documenten.lezen"])
    document = drc_client.retrieve("enkelvoudiginformatieobject", url=url)
    return document


def stream_inhoud(url: str) -> Iterator:
    """
    Get the content behind the URL, in an authorized request.
    """
    drc_client = get_drc_client(scopes=["zds.scopes.documenten.lezen"])
    auth_headers = drc_client.auth.credentials()
    with requests.get(url, stream=True, headers=auth_headers) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None):
            logger.debug("Emitting chunk: %s", chunk)
            yield chunk
