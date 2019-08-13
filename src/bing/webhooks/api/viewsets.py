from rest_framework import status, viewsets
from rest_framework.response import Response

from .serializers import NotificatieSerializer


class WebhookViewSet(viewsets.GenericViewSet):
    serializer_class = NotificatieSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.route_notification(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def route_notification(self, data: dict):
        raise NotImplementedError
