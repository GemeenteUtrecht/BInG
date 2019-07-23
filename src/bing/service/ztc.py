import operator
from functools import lru_cache
from typing import List, Tuple

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


@lru_cache()
def get_aanvraag_resultaattypen() -> List[Tuple[str, str]]:
    config = BInGConfig.get_solo()
    ztc_client = get_ztc_client()

    resultaattypen = ztc_client.list(
        "resultaattype", query_params={"zaaktype": config.zaaktype_aanvraag}
    )
    return [
        (resultaattype["url"], resultaattype["omschrijving"])
        for resultaattype in resultaattypen
    ]


@lru_cache()
def get_aanvraag_besluittypen() -> List[Tuple[str, str]]:
    config = BInGConfig.get_solo()
    ztc_client = get_ztc_client()

    config = BInGConfig.get_solo()
    api_config = APIConfig.get_solo()
    ztc_client = get_ztc_client()

    main_catalogus_uuid = api_config.ztc.extra["main_catalogus_uuid"]
    zaaktype_uuid = config.zaaktype_aanvraag.split("/")[-1]

    besluittypen = ztc_client.list(
        "besluittype", catalogus_uuid=main_catalogus_uuid, zaaktype_uuid=zaaktype_uuid
    )
    return [
        (besluittype["url"], besluittype["omschrijving"])
        for besluittype in besluittypen
    ]
