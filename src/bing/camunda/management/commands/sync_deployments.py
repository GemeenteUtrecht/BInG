from django.core.management import BaseCommand

from ...client import Camunda
from ...models import Deployment


class Command(BaseCommand):
    help = "Sync the Camunda deployments to the local database."

    def handle(self, **options):
        client = Camunda()

        deployments = client.request("deployment")
        for deployment in deployments:
            Deployment.objects.update_or_create(
                uuid=deployment["id"], defaults={"name": deployment["name"] or ""}
            )
