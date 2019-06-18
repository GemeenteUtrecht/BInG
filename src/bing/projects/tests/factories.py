import factory

from ..constants import PlanFases, Toetswijzen


class ProjectFactory(factory.django.DjangoModelFactory):
    project_id = factory.Sequence(lambda n: f"bing-{n}")
    name = factory.Faker("text", max_nb_chars=20)
    toetswijze = Toetswijzen.onbekend
    planfase = PlanFases.onbekend

    class Meta:
        model = "projects.Project"


class ProjectAttachmentFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)

    io_type = factory.Faker("url")
    eio_url = factory.Faker("url")

    class Meta:
        model = "projects.ProjectAttachment"
