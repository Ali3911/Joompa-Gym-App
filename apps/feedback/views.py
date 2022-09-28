"""Feedback views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError, transaction

from apps.feedback.models import Feedback
from apps.feedback.serializers import FeedbackSerializer
from apps.utils import response_json

logger = logging.getLogger(__name__)


class FeedbacksView(APIView):
    """FeedbacksView class

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
        """HTTP get request.

        A HTTP api endpoint that get all feedbacks from database.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for all feedbacks, error message otherwise
        """
        try:
            feedbacks = Feedback.objects.all()
            serializers = FeedbackSerializer(feedbacks, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=FeedbackSerializer,
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        """HTTP POST request.

        Save feedbacks along with feedback ranges and feedback values
        ```
        Request body format:
        {
            "name": "Post-Session Energy Level",
            "fv_feedbacks":[
                {"description":"1", "value":1},
                {"description":"2", "value":2}
                            ]
        }
        ```

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if data saves successfully in db, error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            if request.user.is_staff:
                with transaction.atomic():
                    feedback_serializer = FeedbackSerializer(data=request.data)
                    if feedback_serializer.is_valid():
                        feedback_serializer.save()
                        return Response(
                            response_json(status=True, data=None, message="Feedback saved successfully."),
                            status=status.HTTP_201_CREATED,
                        )
                    else:
                        return Response(
                            response_json(status=False, data=feedback_serializer.errors, message=message),
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            else:
                return Response(
                    response_json(
                        status=False, data=None, message="You do not have permission to perform this action"
                    ),
                    status=status.HTTP_403_FORBIDDEN,
                )
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackView(APIView):
    """FeedbackView class

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
        """HTTP get request.

        A HTTP api endpoint that get single feedback against PK from database.

        Parameters
        ----------
        request : django.http.request
        pk : primary key

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for single feedback, error message otherwise
        """
        try:
            feedbacks = self.get_object(pk=pk)
            serializers = FeedbackSerializer(feedbacks)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=FeedbackSerializer,
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def put(self, request, pk):
        """HTTP put request

        A HTTP api endpoint that update single feedback against PK from database.
        ```
        {
            "name": "Post-Session Energy Level",
            "fv_feedbacks":[
                            {"description":"1", "value":1},
                            {"description":"2", "value":2}
                            ]
        }
        ```

        Parameters
        ----------
        request : django.http.request
        pk : primary key

        Returns
        -------
        rest_framework.response.Response
            returns success message if data updated successfully in db, error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            with transaction.atomic():
                feedback_object = self.get_object(pk=pk)
                feedback_serializer = FeedbackSerializer(feedback_object, data=request.data)

                if feedback_serializer.is_valid():
                    feedback_serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Feedback saved successfully."),
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        response_json(status=False, data=feedback_serializer.errors, message=message),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={200: "OK", 404: "Not Found", 500: "Internal Server Error"},
    )
    def delete(self, request, pk):
        """HTTP delete request

        A HTTP api endpoint that delete single feedback against PK from database.

        Parameters
        ----------
        request : django.http.request
        pk : primary key

        Returns
        -------
        rest_framework.response.Response
            returns success message if data deleted successfully in db, error message otherwise
        """
        feedback_object = self.get_object(pk)
        if feedback_object is None:
            return Response(
                response_json(status=False, data=None, message=f"Feedback with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            feedback_object.delete()
            return Response(
                response_json(status=True, data=None, message="Feedback deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """get_object function

        Parameters
        ----------
        pk : primary key

        Returns
        -------
        model object
            return model object against PK from database.
        """
        try:
            feedback = Feedback.objects.get(pk=pk)
            return feedback

        except Feedback.DoesNotExist:
            logger.info(f"Feedback object with the id: {pk} doesn't exist.")
            return None
