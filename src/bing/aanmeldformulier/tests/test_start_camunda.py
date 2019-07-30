import uuid

from django.test import TestCase

import requests_mock

from bing.config.models import APIConfig, BInGConfig
from bing.projects.tests.factories import ProjectAttachmentFactory, ProjectFactory

from ..tasks import start_camunda_process


class CamundaStartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        api_config = APIConfig.get_solo()
        api_config.camunda_root = "http://camunda.utrecht.nl/"
        api_config.save()

        bing_config = BInGConfig.get_solo()
        bing_config.aanvraag_process_key = "bing"
        bing_config.save()

    def test_full_project(self):
        """
        Test the Camunda API interaction from BInG.

        See: https://docs.camunda.org/manual/7.9/reference/rest/process-definition/post-start-process-instance/
        """
        project = ProjectFactory.create()
        attachment = ProjectAttachmentFactory.create(project=project)

        # kick off the thing
        with requests_mock.Mocker() as m:
            instance_id = str(uuid.uuid4())
            m.post(
                "http://camunda.utrecht.nl/engine-rest/process-definition/key/bing/start",
                json={
                    "links": [
                        {
                            "method": "GET",
                            "href": f"http://localhost:8080/rest-test/process-instance/{instance_id}",
                            "rel": "self",
                        }
                    ],
                    "id": instance_id,
                    "definitionId": "aProcessDefinitionId",
                    "businessKey": f"bing-project-{project.project_id}",
                    "tenantId": None,
                    "ended": False,
                    "suspended": False,
                },
            )
            start_camunda_process(project.id)

        request = m.last_request
        self.assertIsNotNone(request)
