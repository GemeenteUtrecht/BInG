import uuid
from unittest.mock import patch

from django.test import TestCase

from .factories import ProjectAttachmentFactory, ProjectFactory

IO_TYPE_URL = f"https://ztc.nl/api/v1/informatieobjecttypen/{uuid.uuid4().hex}"
EIO_URL = f"https://drc.nl/api/v1/informatieobjecten/{uuid.uuid4().hex}"


class ProjectTests(TestCase):
    def test_no_documents(self):
        project = ProjectFactory.create()

        documents = project.get_documents()

        self.assertEqual(documents, [])

    @patch("bing.projects.models.get_drc_client")
    @patch("bing.projects.models.get_aanvraag_iot")
    def test_existing_documents(self, mock_get_aanvraag_iot, mock_get_drc_client):
        project = ProjectFactory.create()
        ProjectAttachmentFactory.create(
            project=project, io_type=IO_TYPE_URL, eio_url=EIO_URL
        )
        mock_get_aanvraag_iot.return_value = [(IO_TYPE_URL, "Bijlage")]
        mock_get_drc_client.return_value.retrieve.side_effect = lambda r, url: {
            "url": url
        }

        documents = project.get_documents()

        self.assertEqual(
            documents,
            [{"document_type": "Bijlage", "informatieobject": {"url": EIO_URL}}],
        )
