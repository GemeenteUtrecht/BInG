from django.urls import path

from .views import (
    AttachmentDownloadView,
    IndexView,
    KalenderView,
    LoginView,
    MeetingDetailView,
    ProjectDetailView,
    ProjectsView,
    ProjectUpdateView,
)

app_name = "medewerkers"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("kalender/", KalenderView.as_view(), name="kalender"),
    path("kalender/<pk>/", MeetingDetailView.as_view(), name="meeting-detail"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("projects/<pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<pk>/update/", ProjectUpdateView.as_view(), name="project-update"),
    path(
        "attachments/<pk>/download/",
        AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
]
