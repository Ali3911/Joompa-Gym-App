"""BodyPart views file."""
import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.body_part.serializers import BodyPart, BodyPartSerializer, ClassificationSerializer
from apps.utils import response_json

logger = logging.getLogger(__name__)


class BodyPartsView(APIView):
    """BodyPartsView class

    This view performs POST and FETCHALL operations for BodyPart

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

        A HTTP endpoint that returns all BodyPart objects

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:

            body_parts = BodyPart.objects.filter(classification=None)
            body_parts_serializer = BodyPartSerializer(body_parts, many=True)
            return Response(
                response_json(status=True, data=body_parts_serializer.data, message=None), status=status.HTTP_200_OK
            )
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            201: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a BodyPart object alongwith its classifications in DB
        It saves the data in the two ways:
        - add body part along with its classifications
        - add a single classification for the body part

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
            data = request.data
            if "classification" in data:
                serializer = ClassificationSerializer(data=data)
            else:
                serializer = BodyPartSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                if isinstance(serializer, BodyPartSerializer):
                    message = "Body Part successfully inserted."
                elif isinstance(serializer, ClassificationSerializer):
                    message = "Classification successfully inserted."
                return Response(response_json(status=True, data=None, message=message), status=status.HTTP_201_CREATED)
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


class BodyPartView(APIView):
    """BodyPartView class

    This view performs GET,PUT and DELETE operations for BodyPart

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """HTTP GET request

        A HTTP endpoint that returns BodyPart object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        body_part = self.get_body_part_object(pk)
        if body_part is None:
            return Response(
                response_json(status=False, data=None, message=f"Body Part object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = BodyPartSerializer(body_part)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description=""),
                "required": openapi.Schema(type=openapi.TYPE_BOOLEAN, description=""),
            },
            responses={
                200: "OK",
                400: "Bad Request",
                404: "Not Found",
                500: "Internal Server Error",
            },
        ),
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates a BodyPart object for provided PK

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
        body_part = self.get_body_part_object(pk)
        if body_part is None:
            return Response(
                response_json(status=False, data=None, message=f"Body Part with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = BodyPartSerializer(body_part, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Body Part successfully updated"),
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
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes a BodyPart object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        body_part = self.get_body_part_object(pk)
        if body_part is None:
            return Response(
                response_json(status=False, data=None, message=f"Body Part with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            body_part.delete()
            return Response(
                response_json(status=True, data=None, message="Body Part deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_body_part_object(self, pk):
        """Internal method for class BaselineAssessmentView

        A class-level method that returns a BodyPart Object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.body_part.models
            returns BodyPart model object if fetched successfully, reuturns None otherwise
        """
        try:
            body_part = BodyPart.objects.get(pk=pk)
            return body_part
        except BodyPart.DoesNotExist:
            logger.info(f"Body Part object with the id: {pk} doesn't exist")
            return None
