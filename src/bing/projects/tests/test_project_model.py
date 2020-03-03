import uuid
from unittest import skip

from django.test import TestCase

from .factories import ProjectAttachmentFactory, ProjectFactory

IO_TYPE_URL = f"https://ztc.nl/api/v1/informatieobjecttypen/{uuid.uuid4().hex}"
EIO_URL = f"https://drc.nl/api/v1/informatieobjecten/{uuid.uuid4().hex}"


class ProjectTests(TestCase):
    def test_no_documents(self):
        project = ProjectFactory.create()

        documents = project.get_documents()

        self.assertEqual(documents, [])

    @skip("documents are not supported now")
    def test_existing_documents(self):
        project = ProjectFactory.create()
        attachment = ProjectAttachmentFactory.create(
            project=project, io_type=IO_TYPE_URL, eio_url=EIO_URL
        )

        documents = project.get_documents()

        self.assertEqual(
            documents,
            [
                {
                    "document_type": "Bijlage",
                    "informatieobject": {"url": EIO_URL},
                    "attachment": attachment,
                }
            ],
        )
