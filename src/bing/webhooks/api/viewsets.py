from rest_framework import status, viewsets
from rest_framework.response import Response

from ..handlers import update_project_for_new_zaak
from .serializers import NotificatieSerializer


class WebhookViewSet(viewsets.GenericViewSet):
    serializer_class = NotificatieSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.route_notification(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def route_notification(self, data: dict):
        if not data["kanaal"] == "zaken":
            return

        if not data["actie"] == "create":
            return

        if not data["resource"] == "zaak":
            return

        update_project_for_new_zaak(data["resource_url"])
