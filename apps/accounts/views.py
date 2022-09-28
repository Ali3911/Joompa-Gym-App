"""Account views file."""
import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import UsersSerializer
from apps.mobile_api.v1.models import UserProfile
from apps.pagination import CustomPagination
from apps.utils import response_json

logger = logging.getLogger(__name__)


class LogoutView(APIView):
    """Logout view class.

    This view logouts the logged user and expires the user token.

    Parameters
    ----------
    APIView : rest_framework.views
    """

    permission_classes = (IsAuthenticated,)

    # pylint: disable=R0201
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="user refresh token"),
            },
            responses={
                205: "Reset Content",
                500: "Internal Server Error",
            },
        ),
    )
    def post(self, request):
        """HTTP POST request.

        A HTTP api endpoint that logouts the user.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if user successfully logouts, error message otherwise
        """
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as err:
            message = "Error occurred while logging out the user."
            logger.exception(message, str(err))
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            return Response(
                response_json(status=True, data=None, message="User logout successfully."),
                status=status.HTTP_205_RESET_CONTENT,
            )


class UsersAPIView(APIView):
    """AllUsersView v class.

    This view provides GET method for class UsersAPIView

    Parameters
    ----------
    APIView : rest_framework.views
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP GET request.

        A HTTP api endpoint that returns all users with basic information

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if user returned succesfully, error message otherwise
        """
        try:
            all_users = UserProfile.objects.all()
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(all_users, request)
            serializer = UsersSerializer(result_page, many=True)
            response_object = paginator.get_paginated_response(data=serializer.data)
            return Response(response_json(status=True, data=response_object, message=None), status=status.HTTP_200_OK)

        except Exception as err:
            message = "Error occurred while fetching data"
            logger.exception(message, str(err))
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
