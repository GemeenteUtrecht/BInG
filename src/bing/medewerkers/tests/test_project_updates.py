from unittest.mock import patch

from django.test import TestCase, TransactionTestCase

from bing.config.models import RequiredDocuments
from bing.meetings.tests.factories import MeetingFactory
from bing.projects.constants import PlanFases, Toetswijzen
from bing.projects.tests.factories import ProjectFactory

from ..forms import ProjectStatusForm, ProjectUpdateForm


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


class ProjectMeetingUpdates(TestCase):
    """
    Test the forms used during meetings to update the status/result of a project.
    """

    STATUSTYPEN = [
        ("https://example.com/statustypen/1", "Status 1"),
        ("https://example.com/statustypen/2", "Status 2"),
    ]

    RESULTAATTYPEN = [
        ("https://example.com/resultaattypen/1", "Resultaat 1"),
        ("https://example.com/resultaattypen/2", "Resultaat 2"),
    ]

    def setUp(self):
        super().setUp()

        # install mocks
        st_patcher = patch(
            "bing.medewerkers.forms.get_aanvraag_statustypen",
            return_value=self.STATUSTYPEN,
        )
        self.st_mock = st_patcher.start()
        self.addCleanup(st_patcher.stop)

        rt_patcher = patch(
            "bing.medewerkers.forms.get_aanvraag_resultaattypen",
            return_value=self.RESULTAATTYPEN,
        )
        self.rt_mock = rt_patcher.start()
        self.addCleanup(rt_patcher.stop)

    def test_result_optional(self):
        form = ProjectStatusForm(data={"status": "https://example.com/statustypen/1"})

        valid = form.is_valid()

        self.assertTrue(valid)

    def test_result_given(self):
        form = ProjectStatusForm(
            data={
                "status": "https://example.com/statustypen/1",
                "resultaat": "https://example.com/resultaattypen/2",
            }
        )

        valid = form.is_valid()

        self.assertTrue(valid)

    def test_not_final_status_without_result(self):
        form = ProjectStatusForm(data={"status": "https://example.com/statustypen/2"})

        valid = form.is_valid()

        self.assertFalse(valid)
        self.assertIn("status", form.errors)

    def test_final_status_with_result_given(self):
        form = ProjectStatusForm(
            data={
                "status": "https://example.com/statustypen/2",
                "resultaat": "https://example.com/resultaattypen/2",
            }
        )

        valid = form.is_valid()

        self.assertTrue(valid)
