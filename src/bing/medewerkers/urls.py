from django.urls import path

from .views import IndexView, KalenderView

app_name = "medewerkers"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("kalender/", KalenderView.as_view(), name="kalender"),
]
