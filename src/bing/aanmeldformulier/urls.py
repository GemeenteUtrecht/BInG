from django.urls import path

from .views import (
    ConfirmationView,
    GetMapFeatures,
    GetMapFeaturesBB,
    InfoPageView,
    LocationView,
    MeetingView,
    PlanfaseView,
    SpecifyProjectView,
    ToetswijzeView,
    UploadView,
)

app_name = "aanmeldformulier"

urlpatterns = [
    path("", InfoPageView.as_view(), name="info"),
    path("start/", SpecifyProjectView.as_view(), name="specify-project"),
    path("map/", LocationView.as_view(), name="map"),
    path("map/features/<lng>/<lat>/", GetMapFeatures.as_view(), name="map-features"),
    path("map/features/bb/<bbox>/", GetMapFeaturesBB.as_view(), name="map-features-bb"),
    path("toetswijze/", ToetswijzeView.as_view(), name="toetswijze"),
    path("planfase/", PlanfaseView.as_view(), name="planfase"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("vergadering/", MeetingView.as_view(), name="vergadering"),
    path("bevestiging/", ConfirmationView.as_view(), name="confirmation"),
]
