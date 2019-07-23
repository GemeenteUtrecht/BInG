import operator
from typing import Any, Dict, List

from bing.config.service import get_brc_client

from .ztc import get_aanvraag_besluittypen


def fetch_besluit(url: str) -> Dict[str, Any]:
    """
    Retrieve a single Besluit by URL.
    """
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.lezen"])
    besluit = brc_client.retrieve("besluit", url=url)
    return besluit


def fetch_besluiten(zaak: str) -> List[Dict[str, Any]]:
    """
    Fetch a set of besluiten as efficiently as possible.
    """
    brc_client = get_brc_client(scopes=["zds.scopes.besluiten.lezen"])
    besluiten = brc_client.list("besluit", query_params={"zaak": zaak})
    besluiten = sorted(besluiten, key=operator.itemgetter("datum"))

    besluittypen = dict(get_aanvraag_besluittypen())
    for besluit in besluiten:
        besluit["besluittype"] = besluittypen[besluit["besluittype"]]

    return besluiten
