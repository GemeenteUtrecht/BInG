import json
import uuid
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from freezegun import freeze_time
from zgw_consumers.models import APITypes, Service

from bing.config.models import APIConfig, BInGConfig
from bing.meetings.tests.factories import MeetingFactory
from bing.projects.tasks import start_camunda_process
from bing.projects.tests.factories import ProjectAttachmentFactory, ProjectFactory


class CamundaStartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # set up service config
        zrc = Service.objects.create(
            api_type=APITypes.zrc,
            api_root="https://zrc.nl",
            client_id="foo",
            secret="bar",
        )
        drc = Service.objects.create(
            api_type=APITypes.drc,
            api_root="https://drc.nl",
            client_id="foo",
            secret="bar",
        )
        ztc = Service.objects.create(
            api_type=APITypes.ztc,
            api_root="https://ztc.nl",
            client_id="foo",
            secret="bar",
            extra={"main_catalogus_uuid": str(uuid.uuid4())},
        )
        brc = Service.objects.create(
            api_type=APITypes.brc,
            api_root="https://brc.nl",
            client_id="foo",
            secret="bar",
        )
        nrc = Service.objects.create(
            api_type=APITypes.nrc,
            api_root="https://nrc.nl",
            client_id="foo",
            secret="bar",
        )

        api_config = APIConfig.get_solo()
        api_config.camunda_root = "http://camunda.utrecht.nl/"
        api_config.zrc = zrc
        api_config.drc = drc
        api_config.ztc = ztc
        api_config.brc = brc
        api_config.nrc = nrc
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
