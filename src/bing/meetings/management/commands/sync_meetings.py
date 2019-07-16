from datetime import datetime

from django.core.management import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

from bing.medewerkers.utils import (
    MEETING_END_TIME,
    MEETING_START_TIME,
    fetch_vergadering_zaken,
)
from bing.meetings.models import Meeting


class Command(BaseCommand):
    help = "Sync remote meetings to local database"

    def handle(self, **options):
        zaken = fetch_vergadering_zaken()
        for zaak in zaken:
            start = datetime.combine(parse_date(zaak["startdatum"]), MEETING_START_TIME)
            end = datetime.combine(parse_date(zaak["startdatum"]), MEETING_END_TIME)

            fields = {
                "start": timezone.make_aware(start),
                "end": timezone.make_aware(end),
            }

            self.stdout.write(f"Syncing meeting {zaak['identificatie']}")
            meeting, created = Meeting.objects.get_or_create(
                zaak=zaak["url"], defaults=fields
            )

            if created:
                continue

            fields_changed = []
            for key, value in fields.items():
                current_value = getattr(meeting, key)
                if current_value != value:
                    setattr(meeting, key, value)
                    fields_changed.append(key)

            if fields_changed:
                meeting.save(update_fields=fields_changed)
                self.stdout.write("  Synced.")
            else:
                self.stdout.write("  Nothing to do.")
