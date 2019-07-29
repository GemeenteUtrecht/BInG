from django.core.management import BaseCommand

from ...client import Camunda
from ...models import Deployment, ProcessDefinition


class Command(BaseCommand):
    help = "Sync the Camunda deployments to the local database."

    def handle(self, **options):
        client = Camunda()

        deployments = client.request("deployment")
        for deployment in deployments:
            Deployment.objects.update_or_create(
                uuid=deployment["id"], defaults={"name": deployment["name"] or ""}
            )

        definitions = client.request("process-definition")
        for definition in definitions:
            ProcessDefinition.objects.update_or_create(
                camunda_id=definition["id"],
                defaults={
                    "key": definition["key"],
                    "name": definition["name"],
                    "version": definition["version"],
                },
            )
