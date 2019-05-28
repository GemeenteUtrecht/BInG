from typing import List

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client


def fetch_vergadering_zaken() -> List[dict]:
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client()
    zaken = zrc_client.list(
        "zaak", query_params={"zaaktype": config.zaaktype_vergadering}
    )
    return zaken["results"]
