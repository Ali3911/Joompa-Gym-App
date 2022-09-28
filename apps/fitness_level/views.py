"""FitnessLevel views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fitness_level.models import FitnessLevel
from apps.fitness_level.serializers import FitnessLevelSerializer
from apps.mobile_api.v1.models import UserProfile
from apps.utils import response_json, user_profile_data_exists

logger = logging.getLogger(__name__)


class FitnessLevelView(APIView):
    """FitnessLevelView class

    This view performs GET,PUT and DELETE operations for FitnessLevel

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "OK",
            400: "Bad Request",
        },
    )
    def get(self, request, pk):
        """HTTP GET request

        A HTTP endpoint that returns FitnessLevel object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        fitness_level = self.get_object(pk)
        if fitness_level is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Fitness level object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = FitnessLevelSerializer(fitness_level)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=FitnessLevelSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
        },
    )
    def put(self, request, pk):

        """HTTP PUT request

        A HTTP endpoint that updates a FitnessLevel object for provided PK

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
        inacitive_msg = f"You cannot deactivate Fitness level  with id: {pk} because it is being used in mobile app"
        fitness_level = self.get_object(pk)
        if fitness_level is None:
            return Response(
                response_json(status=False, data=None, message=f"Fitness level with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data["required"] is False:
            if user_profile_data_exists("fitness_level", pk, UserProfile):
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=inacitive_msg,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            serializer = FitnessLevelSerializer(fitness_level, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Fitness level successfully updated"),
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
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes a FitnessLevel object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        fitness_level = self.get_object(pk)
        if fitness_level is None:
            return Response(
                response_json(status=False, data=None, message=f"Fitness level with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            fitness_level.delete()
            return Response(
                response_json(status=True, data=None, message="Fitness level deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """Internal method for class FitnessLevelView

        A class-level method that returns a FitnessLevel Object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.fitness_level.models
            returns FitnessLevel model object if fetched successfully, reuturns None otherwise
        """
        try:
            fitness_level = FitnessLevel.objects.get(pk=pk)
            return fitness_level

        except FitnessLevel.DoesNotExist:
            logger.info(f"FitnessLevel object with the id: {pk} doesn't exist.")
            return None


class FitnessLevelsView(APIView):
    """FitnessLevelsView class

    This view performs POST and FETCHALL operations for FitnessLevel

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

        A HTTP endpoint that returns all FitnessLevel objects
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
            fitness_levels = None
            if request.user.is_staff:
                fitness_levels = FitnessLevel.objects.all()

            else:
                fitness_levels = FitnessLevel.objects.filter(required=True)

            serializers = FitnessLevelSerializer(fitness_levels, many=True)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        else:
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=FitnessLevelSerializer,
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a FitnessLevel object  in DB


        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns success message if data saved successfully,error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            if request.user.is_staff:
                serializer = FitnessLevelSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Fitness level saved successfully."),
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
