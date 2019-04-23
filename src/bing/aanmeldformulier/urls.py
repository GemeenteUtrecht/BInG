from django.urls import path

from .views import InfoPageView, SpecifyProjectView, ToetswijzeView

app_name = "aanmeldformulier"

urlpatterns = [
    path("", InfoPageView.as_view(), name="info"),
    path("start/", SpecifyProjectView.as_view(), name="specify-project"),
    path("toetswijze/", ToetswijzeView.as_view(), name="toetswijze"),
]
