from rest_framework import routers

from .viewsets import WebhookViewSet

router = routers.DefaultRouter()
router.register("callbacks", WebhookViewSet, basename="callbacks")

urlpatterns = router.urls
