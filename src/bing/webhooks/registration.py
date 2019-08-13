from django.contrib.sites.models import Site

from glom import T, glom

from bing.accounts.models import User
from bing.config.service import get_nrc_client

from .models import Webhook
from .subscriptions import SUBSCRIPTIONS


def register_webhooks():
    webhooks = {webhook.key: webhook for webhook in Webhook.objects.all()}

    client = get_nrc_client()
    site = Site.objects.get_current()
    default_user = User.objects.filter(auth_token__isnull=False).first()

    for sub in SUBSCRIPTIONS:
        webhook = webhooks.get(sub.key, Webhook(key=sub.key, user=default_user))
        if webhook._subscription:
            continue

        body = {
            "callbackUrl": f"http://{site.domain}{sub.url}",
            "auth": f"Token {webhook.user.auth_token.key}",
            "kanalen": glom(
                sub.channels, [{"naam": "name", "filters": T.get_filters()}]
            ),
        }

        abo = client.create("abonnement", body)

        webhook._subscription = abo["url"]
        webhook.save()
