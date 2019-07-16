import re
import uuid

from django.core.management import BaseCommand

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client
from bing.projects.models import Project

RE_NAME = re.compile(r"BInG aanvraag voor (?P<name>.*)")
RE_PROJECT_ID = re.compile(r"BING-(?P<project_id>.*)")


class Command(BaseCommand):
    help = "Sync remote projects to local database"

    def handle(self, **options):
        config = BInGConfig.get_solo()
        zrc_client = get_zrc_client(
            scopes=["zds.scopes.zaken.lezen"], zaaktypes=[config.zaaktype_aanvraag]
        )
        zaken = zrc_client.list(
            "zaak", query_params={"zaaktype": config.zaaktype_aanvraag}
        )[
            "results"
        ]  # TODO: handle extra pages

        for zaak in zaken:
            match_project_id = RE_PROJECT_ID.match(zaak["identificatie"])
            project_id = (
                match_project_id.group("project_id")
                if match_project_id
                else str(uuid.uuid4())
            )

            match_name = RE_NAME.match(zaak["omschrijving"])
            name = match_name.group("name") if match_name else "UNKNOWN"

            fields = {"project_id": project_id, "name": name}

            self.stdout.write(f"Syncing project {zaak['identificatie']}")
            project, created = Project.objects.get_or_create(
                zaak=zaak["url"], defaults=fields
            )

            if created:
                continue

            fields_changed = []
            for key, value in fields.items():
                current_value = getattr(project, key)
                if current_value != value:
                    setattr(project, key, value)
                    fields_changed.append(key)

            if fields_changed:
                project.save(update_fields=fields_changed)
                self.stdout.write("  Synced.")
            else:
                self.stdout.write("  Nothing to do.")
