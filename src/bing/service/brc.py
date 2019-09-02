import concurrent.futures
import operator
from collections import defaultdict
from typing import Any, Dict, List

from bing.config.service import get_brc_client

from .drc import fetch_document
from .ztc import get_aanvraag_besluittypen


def fetch_besluit(url: str) -> Dict[str, Any]:
    """
    Retrieve a single Besluit by URL.
    """
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.lezen"])
    besluit = brc_client.retrieve("besluit", url=url)
    return besluit


def fetch_besluitinformatieobjecten(besluit: dict) -> List[Dict[str, Any]]:
    """
    Look up the attachments for a Besluit and fetch the documents.

    Return structure looks like:
    [
        {
            "url": <url>,
            "besluit": <url>,
            "informatieobject": {
                "url": <url>,
                "identificatie": <str>,
                ...
            }
        },
    ]
    """
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.lezen"])
    uuid = besluit["url"].rsplit("/")[-1]

    bios = brc_client.list("besluitinformatieobject", besluit_uuid=uuid)

    # fetch related docs
    num_workers = len(bios)
    if num_workers:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = [
                pool.submit(fetch_document, bio["informatieobject"]) for bio in bios
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        documents = {document["url"]: document for document in results}
        for bio in bios:
            bio["informatieobject"] = documents[bio["informatieobject"]]

    return bios


def fetch_besluiten(zaak: str) -> List[Dict[str, Any]]:
    """
    Fetch a set of besluiten with the related data.
    """
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.lezen"])
    besluiten = brc_client.list("besluit", query_params={"zaak": zaak})
    besluiten = sorted(besluiten, key=operator.itemgetter("datum"))

    besluittypen = dict(get_aanvraag_besluittypen())

    # fetch the related documents
    num_workers = len(besluiten)
    if num_workers:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = [
                pool.submit(fetch_besluitinformatieobjecten, besluit)
                for besluit in besluiten
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
    else:
        results = []

    bios_per_besluit = defaultdict(list)
    for bio in sum(results, []):
        bios_per_besluit[bio["besluit"]].append(bio)

    for besluit in besluiten:
        besluit["besluittype"] = besluittypen[besluit["besluittype"]]
        besluit["documents"] = bios_per_besluit[besluit["url"]]

    return besluiten
