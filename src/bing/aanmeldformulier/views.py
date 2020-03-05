import logging

from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView

import requests
from extra_views import ModelFormSetView

from bing.config.models import BInGConfig
from bing.projects.constants import Toetswijzen
from bing.projects.models import Project, ProjectAttachment
from bing.projects.tasks import start_camunda_process

from .bag import get_panden
from .constants import PROJECT_SESSION_KEY, Steps
from .decorators import project_required
from .forms import (
    ProjectAttachmentForm,
    ProjectAttachmentFormSet,
    ProjectBAGForm,
    ProjectGetOrCreateForm,
    ProjectMeetingForm,
    ProjectPlanfaseForm,
    ProjectToetswijzeForm,
)

logger = logging.getLogger(__name__)


class ProjectMixin:
    def get_project(self, queryset=None):
        if queryset is None:
            queryset = Project.objects.all()

        project_id = self.request.session[PROJECT_SESSION_KEY]
        return queryset.get(id=project_id)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("project", self.get_project())
        return super().get_context_data(**kwargs)


class InfoPageView(TemplateView):
    template_name = "aanmeldformulier/info.html"


class SpecifyProjectView(FormView):
    form_class = ProjectGetOrCreateForm
    template_name = "aanmeldformulier/specify_project.html"
    success_url = reverse_lazy("aanmeldformulier:map")
    current_step = Steps.info

    def get_initial(self):
        initial = super().get_initial()
        project_pk = self.request.session.get(PROJECT_SESSION_KEY)
        if project_pk:
            project = Project.objects.filter(pk=project_pk).first()
            if project:
                initial["project_id"] = project.project_id
        return initial

    @transaction.atomic()
    def form_valid(self, form):
        project = form.save()
        self.request.session[PROJECT_SESSION_KEY] = project.id
        return super().form_valid(form)


@method_decorator(project_required, name="dispatch")
class LocationView(ProjectMixin, FormView):
    form_class = ProjectBAGForm
    template_name = "aanmeldformulier/map.html"
    success_url = reverse_lazy("aanmeldformulier:toetswijze")
    current_step = Steps.location

    def form_valid(self, form):
        self.request.session["bag_urls"] = form.cleaned_data["bag_urls"]
        return super().form_valid(form)


@method_decorator(project_required, name="dispatch")
class ToetswijzeView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectToetswijzeForm
    template_name = "aanmeldformulier/toetswijze.html"
    success_url = reverse_lazy("aanmeldformulier:planfase")
    current_step = Steps.toetswijze

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)


@method_decorator(project_required, name="dispatch")
class PlanfaseView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectPlanfaseForm
    template_name = "aanmeldformulier/planfase.html"
    success_url = reverse_lazy("aanmeldformulier:vergadering")
    current_step = Steps.planfase

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)

    def form_valid(self, form):
        response = super().form_valid(form)
        project = self.get_project()
        if project.toetswijze == Toetswijzen.versneld:
            start_camunda_process.delay(
                project.id, bag_urls=self.request.session.get("bag_urls", [])
            )
        return response


@method_decorator(project_required, name="dispatch")
class UploadView(ProjectMixin, ModelFormSetView):
    model = ProjectAttachment
    queryset = ProjectAttachment.objects.none()
    form_class = ProjectAttachmentForm
    formset_class = ProjectAttachmentFormSet
    factory_kwargs = {"extra": 3}
    template_name = "aanmeldformulier/upload.html"
    success_url = reverse_lazy("aanmeldformulier:vergadering")
    # current_step = Steps.upload

    # TODO: Simple cache....
    _req_doc_types = []

    def get_required_document_types(self):
        if not self._req_doc_types:
            required_io_types = []
            project = self.get_project()
            # FIXME get required types
            # io_types = get_aanvraag_iot()
            #
            # try:
            #     io_types_config = RequiredDocuments.objects.get(
            #         toetswijze=project.toetswijze
            #     )
            # except RequiredDocuments.DoesNotExist:
            #     logger.warning(
            #         "No RequiredDocuments for toetswijze '%s' configured",
            #         project.toetswijze,
            #     )
            # else:
            #     required_io_types = [
            #         (io_type, label)
            #         for io_type, label in io_types
            #         if io_type in io_types_config.informatieobjecttypen
            #     ]
            self._req_doc_types = required_io_types
        return self._req_doc_types

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["project"] = self.get_project()

        kwargs["initial"] = [
            {"io_type": doc_type[0]} for doc_type in self.get_required_document_types()
        ]
        return kwargs

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs["extra"] = len(self.get_required_document_types())
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["attachments"] = project.get_documents()
        return context

    def formset_valid(self, form):
        response = super().formset_valid(form)
        project = self.get_project()
        if project.toetswijze == Toetswijzen.versneld:
            start_camunda_process.delay(
                project.id, bag_urls=self.request.session.get("bag_urls", [])
            )
        return response


@method_decorator(project_required, name="dispatch")
class MeetingView(ProjectMixin, UpdateView):
    model = Project
    form_class = ProjectMeetingForm
    template_name = "aanmeldformulier/meeting.html"
    success_url = reverse_lazy("aanmeldformulier:confirmation")
    current_step = Steps.meeting

    def get_object(self, queryset=None):
        return self.get_project(queryset=queryset)

    def get(self, request, *args, **kwargs):
        self.object = project = self.get_project()

        # shortcut - this step isn't needed
        if project.toetswijze == Toetswijzen.versneld:
            return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        start_camunda_process.delay(
            self.object.id, bag_urls=self.request.session.get("bag_urls", [])
        )
        return response


@method_decorator(project_required, name="dispatch")
class ConfirmationView(ProjectMixin, TemplateView):
    """
    Show the confirmation page.

    TODO: set up ajax polling/notification when the Zaak has been created so
    that the identification can be displayed.
    """

    template_name = "aanmeldformulier/confirmation.html"
    current_step = Steps.confirmation

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        del self.request.session[PROJECT_SESSION_KEY]
        return response


class GetMapFeatures(View):
    def get(self, request, lng, lat, *args, **kwargs):
        data = {"query": {"lat": lat, "lng": lng}}
        geojson_point = {"type": "Point", "coordinates": [lat, lng]}
        data["features"] = get_panden(geojson_point)
        return JsonResponse(data)


class GetMapFeaturesBB(View):
    def get(self, request, bbox, *args, **kwargs):
        """
        Relay a GeoJSON query to BPTL.
        """
        config = BInGConfig.get_solo()

        response = requests.post(
            f"{config.bptl_root}/api/v1/work-unit",
            json={"topic": "TODO", "vars": {}},
            headers={"Authorization": f"Token {config.bptl_token}"},
        )

        response.raise_for_status()

        import bpdb

        bpdb.set_trace()

        data = {"features": []}
        return JsonResponse(data)
