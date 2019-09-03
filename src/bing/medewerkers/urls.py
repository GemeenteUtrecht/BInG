from django.urls import path

from .views import (
    AttachmentDownloadView,
    DetermineProcedureView,
    HandleTaskView,
    IndexView,
    KalenderView,
    LoginView,
    MeetingDetailView,
    ProjectBesluitCreate,
    ProjectDetailView,
    ProjectsView,
    ProjectUpdateView,
    UserTasksView,
)

app_name = "medewerkers"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("kalender/", KalenderView.as_view(), name="kalender"),
    path("kalender/<pk>/", MeetingDetailView.as_view(), name="meeting-detail"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("projects/<pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<pk>/besluit/", ProjectBesluitCreate.as_view(), name="project-besluit"
    ),
    path("projects/<pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path(
        "attachments/<pk>/download/",
        AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
    path("tasks/", UserTasksView.as_view(), name="tasks"),
    path("tasks/handle/<uuid:task_id>/", HandleTaskView.as_view(), name="handle-task"),
    # TODO: build a generic task router
    path(
        "tasks/<pk>/<uuid:task_id>/",
        DetermineProcedureView.as_view(),
        name="task-determine-procedure",
    ),
]
