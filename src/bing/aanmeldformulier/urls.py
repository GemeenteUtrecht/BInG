from django.urls import path

from .views import InfoPageView

app_name = "aanmeldformulier"

urlpatterns = [path("", InfoPageView.as_view(), name="info")]
