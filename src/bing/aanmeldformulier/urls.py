from django.urls import path

from .views import InfoPageView, SpecifyProjectView

app_name = "aanmeldformulier"

urlpatterns = [
    path("", InfoPageView.as_view(), name="info"),
    path("start/", SpecifyProjectView.as_view(), name="specify-project"),
]
