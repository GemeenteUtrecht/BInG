from zds_client import Client

from .models import APIConfig


def get_drc_client(**claims) -> Client:
    config = APIConfig.get_solo()
    client = config.get_drc_client()
    if claims:
        client.auth.set_claims(**claims)
    return client
