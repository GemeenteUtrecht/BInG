from typing import Dict

from django.conf import settings as django_settings

from zds_client import Client
from zds_client.log import Log


def settings(request):
    public_settings = (
        "GOOGLE_ANALYTICS_ID",
        "ENVIRONMENT",
        "SHOW_ALERT",
        "PROJECT_NAME",
    )

    context = {
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        )
    }

    if hasattr(django_settings, "RAVEN_CONFIG"):
        context.update(dsn=django_settings.RAVEN_CONFIG.get("public_dsn", ""))

    return context


def client_log(request) -> Dict[str, Log]:
    log = Client._log
    total_duration = sum(entry["duration"] for entry in log.entries())
    return {"client_log": log, "total_duration_api_calls": total_duration}
