from unittest.mock import patch

from django.test import TransactionTestCase

from bing.config.models import RequiredDocuments
from bing.meetings.tests.factories import MeetingFactory
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.tests.factories import ProjectFactory

from ..forms import ProjectUpdateForm


class ProjectToetswijzeUpdateTests(TransactionTestCase):
    """
    Test the business logic if the toetswijze changes.
    """

    def setUp(self):
        super().setUp()

        RequiredDocuments.objects.create(
            toetswijze=Toetswijzen.regulier, informatieobjecttypen=[]
        )
        RequiredDocuments.objects.create(
            toetswijze=Toetswijzen.versneld, informatieobjecttypen=[]
        )

    @patch("bing.medewerkers.forms.add_project_to_meeting")
    def test_toetwijze_initially_empty_to_regular_no_meeting(self, mock_add_project):
        project = ProjectFactory.create(toetswijze=Toetswijzen.onbekend)
        form = ProjectUpdateForm(
            data={
                "toetswijze": Toetswijzen.regulier,
                "planfase": PlanFases.do,
                "meeting": None,
            },
            instance=project,
        )
        self.assertTrue(form.is_valid())

        form.save()

        mock_add_project.delay.assert_not_called()

    @patch("bing.medewerkers.forms.add_project_to_meeting")
    def test_toetwijze_initially_empty_to_regular_with_meeting(self, mock_add_project):
        project = ProjectFactory.create(toetswijze=Toetswijzen.onbekend)
        meeting = MeetingFactory.create(
            zaak="https://ref.tst.vng.cloud/zrc/api/v1/zaken/foobar"
        )
        form = ProjectUpdateForm(
            data={
                "toetswijze": Toetswijzen.regulier,
                "planfase": PlanFases.do,
                "meeting": meeting.id,
            },
            instance=project,
        )
        self.assertTrue(form.is_valid())

        form.save()

        mock_add_project.delay.assert_called_once_with(meeting.id, project.id)

    @patch("bing.medewerkers.forms.add_project_to_meeting")
    def test_toetwijze_initially_empty_to_versneld_no_meeting(self, mock_add_project):
        project = ProjectFactory.create(toetswijze=Toetswijzen.onbekend)
        form = ProjectUpdateForm(
            data={
                "toetswijze": Toetswijzen.versneld,
                "planfase": PlanFases.do,
                "meeting": None,
            },
            instance=project,
        )
        self.assertTrue(form.is_valid())

        form.save()

        mock_add_project.delay.assert_not_called()

    @patch("bing.medewerkers.forms.remove_project_from_meeting")
    @patch("bing.medewerkers.forms.add_project_to_meeting")
    def test_toetwijze_initially_empty_to_versneld_with_meeting(
        self, mock_add_project, mock_remove_project_from_meeting
    ):
        meeting = MeetingFactory.create(
            zaak="https://ref.tst.vng.cloud/zrc/api/v1/zaken/foobar"
        )
        project = ProjectFactory.create(
            toetswijze=Toetswijzen.onbekend, meeting=meeting
        )
        form = ProjectUpdateForm(
            data={"toetswijze": Toetswijzen.versneld, "planfase": PlanFases.do},
            instance=project,
        )
        self.assertTrue(form.is_valid())

        form.save()

        mock_add_project.delay.assert_not_called()
        mock_remove_project_from_meeting.delay.assert_called_once_with(
            meeting.id, project.id
        )

    def test_no_notify_toetswijze_unchanged(self):
        project = ProjectFactory.create(toetswijze=Toetswijzen.versneld)
        form = ProjectUpdateForm(
            data={"toetswijze": Toetswijzen.versneld, "planfase": PlanFases.do},
            instance=project,
        )
        self.assertTrue(form.is_valid())

        with patch.object(project, "notify", autospec=True) as mock_notify:
            form.save()

        mock_notify.assert_not_called()
