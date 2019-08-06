import json
import uuid

from django.test import TestCase

import requests_mock
from freezegun import freeze_time

from bing.config.models import APIConfig, BInGConfig
from bing.meetings.tests.factories import MeetingFactory
from bing.projects.tests.factories import ProjectAttachmentFactory, ProjectFactory

from ..tasks import start_camunda_process


class CamundaStartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        api_config = APIConfig.get_solo()
        api_config.camunda_root = "http://camunda.utrecht.nl/"
        api_config.save()

        cls.zaaktype = f"https://ztc.utrecht.nl/zaaktype/{uuid.uuid4()}"

        bing_config = BInGConfig.get_solo()
        bing_config.zaaktype_aanvraag = cls.zaaktype
        bing_config.aanvraag_process_key = "bing"
        bing_config.save()

    @freeze_time("2019-07-30 14:00")
    def test_full_project(self):
        """
        Test the Camunda API interaction from BInG.

        See: https://docs.camunda.org/manual/7.9/reference/rest/process-definition/post-start-process-instance/
        """
        config = BInGConfig.get_solo()
        meeting = MeetingFactory.create()
        project = ProjectFactory.create(meeting=meeting)
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

        # check request contents
        self.assertEqual(
            request.url,
            "http://camunda.utrecht.nl/engine-rest/process-definition/key/bing/start",
        )

        expected_body = {
            "businessKey": f"bing-project-{project.project_id}",
            "withVariablesInReturn": False,
            "variables": {
                "zaak": {
                    "type": "Json",
                    "value": json.dumps(
                        {
                            "bronorganisatie": config.organisatie_rsin,
                            "identificatie": f"BInG-{project.project_id}",
                            "zaaktype": config.zaaktype_aanvraag,
                            "verantwoordelijkeOrganisatie": config.organisatie_rsin,
                            "startdatum": "2019-07-30",
                            "omschrijving": f"BInG aanvraag voor {project.name}",
                        }
                    ),
                },
                "projectId": {"value": project.project_id, "type": "String"},
                "toetswijze": {"value": project.toetswijze, "type": "String"},
                "documenten": {
                    "value": json.dumps([attachment.eio_url]),
                    "type": "Json",
                },
            },
        }
        self.assertEqual(request.json(), expected_body)

        project.refresh_from_db()
        self.assertEqual(project.camunda_process_instance_id, instance_id)
        self.assertEqual(
            project.camunda_process_instance_url,
            f"http://localhost:8080/rest-test/process-instance/{instance_id}",
        )
