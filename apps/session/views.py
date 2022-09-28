"""Session views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.session.models import Session
from apps.session.serializers import SessionSerializer
from apps.utils import response_json

logger = logging.getLogger(__name__)


class SessionView(APIView):
    """SessionView class

    This view performs GET,PUT and DELETE operations for Session

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """HTTP GET request

        A HTTP endpoint that returns a Session object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        session = self.get_object(pk=pk)
        if session is None:
            return Response(
                response_json(status=False, data=None, message=f"Session object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = SessionSerializer(session)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=SessionSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates a Session object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data updated successfully,error message otherwise
        """
        message = "Error occurred while updating the data in the database."
        session = self.get_object(pk=pk)
        if session is None:
            return Response(
                response_json(status=False, data=None, message=f"Session with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = SessionSerializer(session, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Session successfully updated"),
                    status=status.HTTP_200_OK,
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

    @swagger_auto_schema(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes a Session object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        session = self.get_object(pk=pk)
        if session is None:
            return Response(
                response_json(status=False, data=None, message=f"Session with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            session.delete()
            return Response(
                response_json(status=True, data=None, message="Session deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """Internal method for class SessionView

        A class-level method that returns a Session object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.session.models
            returns Session model object if fetched successfully, reuturns None otherwise
        """

        try:
            return Session.objects.get(pk=pk)

        except Session.DoesNotExist:
            logger.info(f"Session object with the id: {pk} doesn't exist")
            return None


class SessionsView(APIView):
    """SessionsView class

    This view performs POST and FETCHALL operations for Session

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP GET request

        A HTTP endpoint that returns all Session objects

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:
            sessions = Session.objects.all()
            serializers = SessionSerializer(sessions, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=SessionSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a Session object in DB


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
            if request.user.is_staff:
                serializer = SessionSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Session object has saved successfully."),
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        response_json(status=False, data=serializer.errors, message=message),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    response_json(
                        status=False, data=None, message="You do not have permission to perform this action"
                    ),
                    status=status.HTTP_403_FORBIDDEN,
                )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
