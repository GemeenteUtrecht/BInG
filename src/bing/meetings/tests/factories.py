from django.utils import timezone

import factory


class MeetingFactory(factory.django.DjangoModelFactory):
    start = factory.Faker("future_datetime", tzinfo=timezone.utc)
    end = factory.Faker("future_datetime", tzinfo=timezone.utc)

    class Meta:
        model = "meetings.Meeting"
