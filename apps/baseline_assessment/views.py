"""BaselineAssessment views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.baseline_assessment.models import BaselineAssessment
from apps.baseline_assessment.serializers import BaselineAssessmentSerializer
from apps.mobile_api.v1.models import UserProfile
from apps.utils import response_json, user_profile_data_exists

logger = logging.getLogger(__name__)


class BaselineAssessmentView(APIView):
    """BaselineAssessmentView class

    This view performs GET, PUT and DELETE operations for BaselineAssessment

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

        A HTTP endpoint that returns BaselineAssessment object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        baseline_assessment_object = self.get_object(pk)
        if baseline_assessment_object is None:
            return Response(
                response_json(status=False, data=None, message=f"Baseline assessment with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = BaselineAssessmentSerializer(baseline_assessment_object)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=BaselineAssessmentSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates a BaselineAssessment object for provided PK

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
        inactive_msg = (
            f"You cannot deactivate Baseline assessment with id: {pk} because it is being used in mobile app"
        )
        baseline_assessment_object = self.get_object(pk)
        if baseline_assessment_object is None:
            return Response(
                response_json(status=False, data=None, message=f"Baseline assessment with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data["required"] is False:
            if user_profile_data_exists("baseline_assessment", pk, UserProfile):
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=inactive_msg,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            serializer = BaselineAssessmentSerializer(baseline_assessment_object, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(
                        status=True, data=serializer.data, message="Baseline assessment successfully updated"
                    ),
                    status=status.HTTP_200_OK,
                )
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
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """HTTP DELETE request

        A HTTP endpoint that deletes a BaselineAssessment object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        baseline_assessment_object = self.get_object(pk)
        if baseline_assessment_object is None:
            return Response(
                response_json(status=False, data=None, message=f"Baseline assessment with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            baseline_assessment_object.delete()
            return Response(
                response_json(status=True, data=None, message="Baseline assessment object deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """Internal method for class BaselineAssessmentView

        A class-level method that returns a BaselineAssessment Object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.baseline_assessment.models
            returns BaselineAssessment model object if fetched successfully, reuturns None otherwise
        """
        try:
            return BaselineAssessment.objects.get(pk=pk)
        except BaselineAssessment.DoesNotExist:
            logger.info(f"Baseline assessment object with the id: {pk} doesn't exist")
            return None


class BaselineAssessmentsView(APIView):
    """BaselineAssessmentsView class

    This view performs POST and FETCHALL operations for BaselineAssessment

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP GET request

        A HTTP endpoint that returns all BaselineAssessment objects

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        try:
            baseline_assessment_objects = None
            if request.user.is_staff:
                baseline_assessment_objects = BaselineAssessment.objects.all()
            else:
                baseline_assessment_objects = BaselineAssessment.objects.filter(required=True)

            serializer = BaselineAssessmentSerializer(baseline_assessment_objects, many=True)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=BaselineAssessmentSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a BaselineAssessment object in DB

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
                serializer = BaselineAssessmentSerializer(data=request.data, many=False)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(
                            status=True, data=None, message="Baseline assessment object has saved successfully."
                        ),
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
            message = "Error occurred while saving the data into the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
