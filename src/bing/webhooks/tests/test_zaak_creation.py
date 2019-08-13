from django.urls import reverse_lazy
from django.utils import timezone

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from bing.accounts.models import User
from bing.config.models import BInGConfig
from bing.projects.tests.factories import ProjectFactory

NOTIFICATION = {
    "kanaal": "zaken",
    "hoofdObject": "http://gemma-zrc.k8s.dc1.proeftuin.utrecht.nl/api/v1/zaken/9a32b9ba-cf41-4c35-984e-0f964700aa73",
    "resource": "zaak",
    "resourceUrl": "http://gemma-zrc.k8s.dc1.proeftuin.utrecht.nl/api/v1/zaken/9a32b9ba-cf41-4c35-984e-0f964700aa73",
    "actie": "create",
    "aanmaakdatum": timezone.now().isoformat(),
    "kenmerken": {
        "bronorganisatie": "002220647",
        "zaaktype": (
            "http://gemma-ztc.k8s.proeftuin.utrecht.nl/api/v1/"
            "catalogussen/28487d3f-6a1b-489c-b03d-c75ac6693e72/"
            "zaaktypen/6a916222-61ba-4596-bcca-a2a9c3e1ffe4"
        ),
        "vertrouwelijkheidaanduiding": "openbaar",
    },
}


class ZaakCreationTests(APITestCase):
    url = reverse_lazy("callbacks-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user = User.objects.create(username="foo")
        cls.token = Token.objects.create(user=user).key

        config = BInGConfig.get_solo()
        config.zaaktype_aanvraag = ""

    def setUp(self):
        super().setUp()

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

    def test_project_sync(self):
        project = ProjectFactory.create(project_id="dummy", zaak="")

        response = self.client.post(self.url, NOTIFICATION)

        self.assertEqual(response.status_code, 204)
        project.refresh_from_db()
        self.assertEqual(
            project.zaak,
            "http://gemma-zrc.k8s.dc1.proeftuin.utrecht.nl/api/v1/zaken/9a32b9ba-cf41-4c35-984e-0f964700aa73",
        )
