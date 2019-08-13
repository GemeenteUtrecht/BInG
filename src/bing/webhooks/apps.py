import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class WebhooksConfig(AppConfig):
    name = "bing.webhooks"

    def ready(self):
        from .registration import register_webhooks

        try:
            register_webhooks()
        except Exception:
            logger.exception("Webhook registration failed.")
