from functools import partial

from zds_client import Client

from .models import APIConfig


def get_client(type: str, **claims) -> Client:
    config = APIConfig.get_solo()
    service = getattr(config, type, None)
    if service is None:
        raise ValueError(f"No {type.upper()} configured!")

    client = service.build_client()
    client.auth.user_id = "bing-user"
    client.auth.user_representation = "BInG Gebruiker"
    if claims:
        client.auth.set_claims(**claims)
    return client


get_zrc_client = partial(get_client, "zrc")
get_ztc_client = partial(get_client, "ztc", scopes=["zds.scopes.zaaktypes.lezen"])
get_drc_client = partial(get_client, "drc")
