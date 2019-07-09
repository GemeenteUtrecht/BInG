import concurrent.futures
import operator
from typing import Any, Dict, List, Optional

from django.utils import timezone

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client


def fetch_zaak(url: str) -> Dict[str, Any]:
    """
    Retrieve a single Zaak by URL.
    """
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(scopes=["zds.scopes.zaken.lezen"], zaaktypes=["*"])
    zaak = zrc_client.retrieve("zaak", url=url)
    return zaak


def fetch_zaken(urls: List[str], num_workers: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch a set of zaken as efficiently as possible.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = [pool.submit(fetch_zaak, url) for url in urls]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    results = sorted(results, key=operator.itemgetter("registratiedatum"))
    return results


def fetch_status(url: str) -> Dict[str, Any]:
    """
    Retrieve a single Zaak by URL.
    """
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(scopes=["zds.scopes.zaken.lezen"], zaaktypes=["*"])
    status = zrc_client.retrieve("status", url=url)
    return status


def fetch_resultaat(url: Optional[str]) -> Optional[Dict[str, str]]:
    if not url:
        return None

    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(scopes=["zds.scopes.zaken.lezen"], zaaktypes=["*"])
    resultaat = zrc_client.retrieve("resultaat", url=url)
    return resultaat


def set_status(zaak_url: str, statustype_url: str, **extra) -> Dict[str, str]:
    assert "zaak" not in extra
    assert "statusType" not in extra

    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(
        scopes=["zds.scopes.statussen.toevoegen"], zaaktypes=["*"]
    )

    defaults = {"datumStatusGezet": timezone.now().isoformat()}
    defaults.update(**extra)

    body = {"zaak": zaak_url, "statusType": statustype_url}
    body.update(**defaults)

    status = zrc_client.create("status", body)
    return status


def set_resultaat(
    zaak_url: str, resultaattype_url: str, toelichting: str = ""
) -> Dict[str, str]:
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(scopes=["zds.scopes.zaken.bijwerken"], zaaktypes=["*"])

    body = {
        "zaak": zaak_url,
        "resultaatType": resultaattype_url,
        "toelichting": toelichting,
    }

    resultaat = zrc_client.create("resultaat", body)
    return resultaat
