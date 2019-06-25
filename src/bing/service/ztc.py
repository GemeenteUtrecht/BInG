import operator
from functools import lru_cache
from typing import Any, Dict, List, Tuple

from bing.config.models import APIConfig, BInGConfig
from bing.config.service import get_ztc_client


@lru_cache()
def get_aanvraag_iot() -> List[Tuple[str, str]]:
    config = BInGConfig.get_solo()
    api_config = APIConfig.get_solo()
    ztc_client = get_ztc_client()

    zaaktype = ztc_client.retrieve("zaaktype", url=config.zaaktype_aanvraag)
    main_catalogus_uuid = api_config.ztc.extra["main_catalogus_uuid"]
    informatieobjecttypen = ztc_client.list(
        "informatieobjecttype", catalogus_uuid=main_catalogus_uuid
    )
    informatieobjecttypen = [
        iot
        for iot in informatieobjecttypen
        if iot["url"] in zaaktype["informatieobjecttypen"]
    ]

    iot_choices = [(iot["url"], iot["omschrijving"]) for iot in informatieobjecttypen]
    return iot_choices


def fetch_statustype(url: str) -> Dict[str, Any]:
    ztc_client = get_ztc_client()
    statustype = ztc_client.retrieve("statustype", url=url)
    return statustype


@lru_cache()
def get_aanvraag_statustypen() -> List[Tuple[str, str]]:
    config = BInGConfig.get_solo()
    api_config = APIConfig.get_solo()
    ztc_client = get_ztc_client()

    main_catalogus_uuid = api_config.ztc.extra["main_catalogus_uuid"]
    zaaktype_uuid = config.zaaktype_aanvraag.split("/")[-1]

    statustypen = ztc_client.list(
        "statustype", catalogus_uuid=main_catalogus_uuid, zaaktype_uuid=zaaktype_uuid
    )

    return [
        (statustype["url"], statustype["omschrijving"])
        for statustype in sorted(statustypen, key=operator.itemgetter("volgnummer"))
    ]
