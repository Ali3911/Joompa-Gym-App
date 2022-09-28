import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notification.models import UserNotification
from apps.notification.serializers import UserNotificationSerializer
from apps.utils import response_json

logger = logging.getLogger(__name__)


class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=UserNotificationSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves an Notification object  in DB


        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns success message if data saved successfully,error message otherwise
        """
        message = "Error occurred while saving the data into the database"
        try:
            data = request.data
            existing_user_notification = UserNotification.objects.filter(
                user_profile_id=data["user_profile_id"], registration_id=data["registration_id"]
            )
            if existing_user_notification.exists():
                existing_user_notification.update(
                    user_profile_id=data["user_profile_id"], registration_id=data["registration_id"]
                )
            else:
                serializer = UserNotificationSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Notification successfully inserted."),
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        response_json(status=False, data=serializer.errors, message=message),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
