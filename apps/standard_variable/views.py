"""StandardVariable views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mobile_api.v1.models import UserStandardVariable
from apps.standard_variable.models import StandardVariable
from apps.standard_variable.serializers import StandaradVariableSerializer
from apps.utils import response_json, user_profile_data_exists

logger = logging.getLogger(__name__)


class StandardVariableView(APIView):
    """StandardVariableView class

    This view performs GET,PUT and DELETE operations for StandardVariable

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
    def get(self, request, pk):
        """HTTP GET request

        A HTTP endpoint that returns a StandardVariable object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        standard_variable_obj = self.get_object(pk=pk)
        if standard_variable_obj is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Standard variable object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = StandaradVariableSerializer(standard_variable_obj)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=StandaradVariableSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates a StandardVariable object for provided PK

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
        inactive_msg = f"You cannot deactivate Standard variable with id: {pk} because it is being used in mobile app"
        standard_variable_obj = self.get_object(pk=pk)
        if standard_variable_obj is None:
            return Response(
                response_json(status=False, data=None, message=f"Standard variable with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data["required"] is False:
            if user_profile_data_exists("standard_variable_id", pk, UserStandardVariable):
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=inactive_msg,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            serializer = StandaradVariableSerializer(standard_variable_obj, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Standard Variable successfully updated"),
                    status=status.HTTP_200_OK,
                )
            return Response(
                response_json(status=False, data=serializer.errors, message=message),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            message = "Error occurred while updating the data in the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes a StandardVariable object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        standard_variable_obj = self.get_object(pk=pk)
        if standard_variable_obj is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Standard variable object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            standard_variable_obj.delete()
            return Response(
                response_json(status=True, data=None, message="Standard variable object deleted successfully."),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """Internal method for class StandardVariableView

        A class-level method that returns a StandardVariable object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.standard_variable.models
            returns StandardVariable model object if fetched successfully, reuturns None otherwise
        """
        try:
            return StandardVariable.objects.get(pk=pk)
        except StandardVariable.DoesNotExist:
            logger.info(f"Standard variable object with the id: {pk} doesn't exist")
            return None


class StandardVariablesView(APIView):
    """StandardVariablesView class

    This view performs POST and FETCHALL operations for StandardVariable

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

        A HTTP endpoint that returns all StandardVariable objects

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:
            if request.user.is_staff:
                standard_variables = StandardVariable.objects.all()
            else:
                standard_variables = StandardVariable.objects.filter(required=True)
            serializer = StandaradVariableSerializer(standard_variables, many=True)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=StandaradVariableSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a StandardVariable object in DB


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
                serializer = StandaradVariableSerializer(data=request.data, many=False)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Standard variable has saved successfully."),
                        status=status.HTTP_200_OK,
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
