import json
import uuid
from unittest import skip
from unittest.mock import patch

from django.test import TestCase, override_settings

import requests_mock
from freezegun import freeze_time

from bing.config.models import BInGConfig
from bing.meetings.tests.factories import MeetingFactory
from bing.projects.tasks import start_camunda_process
from bing.projects.tests.factories import ProjectAttachmentFactory, ProjectFactory


@override_settings(CAMUNDA_API_ROOT="engine-rest")
class CamundaStartTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        # set up service config
        cls.zaaktype = f"https://ztc.utrecht.nl/zaaktype/{uuid.uuid4()}"

        bing_config = BInGConfig.get_solo()
        bing_config.zaaktype_aanvraag = cls.zaaktype
        bing_config.aanvraag_process_key = "bing"
        bing_config.save()

    def setUp(self):
        super().setUp()

        patcher = patch("bing.projects.tasks.relate_created_zaak")
        patcher.start()
        self.addCleanup(patcher.stop)

    @skip("skip until the integration with camunda is set")
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
                    "businessKey": f"bing-aanvraag",
                    "tenantId": None,
                    "ended": False,
                    "suspended": False,
                },
            )
            with patch("bing.projects.tasks.ResultSet.ready", return_value=True):
                start_camunda_process(project.id)

        request = m.last_request
        self.assertIsNotNone(request)

        # check request contents
        self.assertEqual(
            request.url,
            "http://camunda.utrecht.nl/engine-rest/process-definition/key/bing/start",
        )

        expected_body = {
            "businessKey": f"bing-aanvraag",
            "withVariablesInReturn": False,
            "variables": {
                "zaak": {
                    "type": "json",
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
                    "valueInfo": {
                        "serializationDataFormat": "application/json",
                        "objectTypeName": "com.gemeenteutrecht.processplatform.domain.impl.ZaakImpl",
                    },
                },
                "projectId": {"value": project.project_id, "type": "String"},
                "toetswijze": {"value": project.toetswijze, "type": "String"},
                "documenten": {
                    "value": json.dumps([attachment.eio_url]),
                    "type": "json",
                    "valueInfo": {
                        "serializationDataFormat": "application/json",
                        "objectTypeName": (
                            "com.gemeenteutrecht.processplatform.domain.document.impl.DocumentImpl"
                        ),
                    },
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
