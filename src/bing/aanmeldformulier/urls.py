from django.urls import path

from .views import InfoPageView, SpecifyProjectView, ToetswijzeView, UploadView

app_name = "aanmeldformulier"

urlpatterns = [
    path("", InfoPageView.as_view(), name="info"),
    path("start/", SpecifyProjectView.as_view(), name="specify-project"),
    path("toetswijze/", ToetswijzeView.as_view(), name="toetswijze"),
    path("upload/", UploadView.as_view(), name="upload"),
]
