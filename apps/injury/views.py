"""Injury views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.injury.models import Injury, InjuryType
from apps.injury.serializers import InjurySerializer, InjuryTypeSerializer
from apps.mobile_api.v1.models import UserInjury
from apps.utils import response_json, user_profile_data_exists

logger = logging.getLogger(__name__)


class InjuryView(APIView):
    """InjuryView class

    This view performs GET,PUT and DELETE operations for Injury

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """HTTP GET request

        A HTTP endpoint that returns an Injury object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        injury = self.get_injury_object(pk=pk)
        if injury is None:
            return Response(
                response_json(status=False, data=None, message=f"Injury object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = InjurySerializer(injury)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=InjurySerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates an Injury object for provided PK

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
        injury = self.get_injury_object(pk=pk)
        if injury is None:
            return Response(
                response_json(status=False, data=None, message=f"Injury with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data["required"] is False:
            if user_profile_data_exists("injury", pk, UserInjury):
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=f"You cannot deactivate Injury with id: {pk} because it is being used in mobile app",
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            serializer = InjurySerializer(injury, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Injury successfully updated"),
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
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes an Injury object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """

        injury = self.get_injury_object(pk=pk)
        if injury is None:
            return Response(
                response_json(status=False, data=None, message=f"Injury with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            injury.delete()
            return Response(
                response_json(status=True, data=None, message="Injury deleted successfully"), status=status.HTTP_200_OK
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_injury_object(self, pk):
        """Internal method for class InjuryView

        A class-level method that returns an Injury Object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.injury.models
            returns Injury model object if fetched successfully, reuturns None otherwise
        """
        try:
            injury = Injury.objects.get(pk=pk)
            return injury
        except Injury.DoesNotExist:
            logger.info(f"Injury object with the id: {pk} doesn't exist")
            return None


class InjuriesView(APIView):
    """InjuriesView class

    This view performs POST and FETCHALL operations for Injury

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

        A HTTP endpoint that returns all Injury objects
        It will be available on both admin and mobile side.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:
            injuries = None
            if request.user.is_staff:
                injuries = Injury.objects.all()
            else:
                injuries = Injury.objects.filter(required=True)

            serializers = InjurySerializer(injuries, many=True)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        else:
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=InjurySerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves an Injury object  in DB


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
                serializer = InjurySerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Injury successfully inserted."),
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


class InjuryTypesView(APIView):
    """InjuryTypesView class

    This view performs FETCHALL operations for InjuryType

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP GET request

        A HTTP endpoint that returns all InjuryType objects

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:
            data = list()
            injury_types = InjuryType.objects.all()

            for injury in injury_types:
                serialize_data = InjuryTypeSerializer(injury).data
                serialize_data["injuries"] = InjurySerializer(injury.injuries_type.all(), many=True).data
                data.append(serialize_data)

            return Response(response_json(status=True, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
