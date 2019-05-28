from django.urls import path

from .views import IndexView, KalenderView, ProductUpdateView, ProjectsView

app_name = "medewerkers"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("kalender/", KalenderView.as_view(), name="kalender"),
    path("projects/", ProjectsView.as_view(), name="projects"),
    path("projects/<pk>/", ProductUpdateView.as_view(), name="project-update"),
]
