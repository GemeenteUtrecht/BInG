from typing import Dict

from zds_client import ClientAuth

from .models import AliasCredential


def get_services(*aliases) -> Dict[str, Dict[str, str]]:
    alias_creds = AliasCredential.objects.filter(alias__in=aliases)

    services = {}

    for creds in alias_creds:
        auth = ClientAuth(creds.client_id, creds.secret)
        header = auth.credentials()["Authorization"]
        services[creds.alias] = {"jwt": header}

    return services
