"""Goal views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Count

from apps.controlled.models import SessionLength
from apps.goal.serializers import Goal, GoalSerializer
from apps.mobile_api.v1.models import UserProfile
from apps.reps_in_reserve.models import RepsRange
from apps.utils import response_json, user_profile_data_exists

logger = logging.getLogger(__name__)


class GoalView(APIView):
    """GoalView class

    This view performs GET,PUT and DELETE operations for Goal

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

        A HTTP endpoint that returns Goal object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        goal = self.get_goal_object(pk)
        if goal is None:
            return Response(
                response_json(status=False, data=None, message=f"Goal object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = GoalSerializer(goal)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=GoalSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP PUT request

        A HTTP endpoint that updates a Goal object for provided PK

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
        goal = self.get_goal_object(pk)
        if goal is None:
            return Response(
                response_json(status=False, data=None, message=f"Goal with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data["required"] is False:
            if user_profile_data_exists("goal", pk, UserProfile):
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=f"You cannot deactivate Goal with id: {pk} because it is being used in mobile app",
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            serializer = GoalSerializer(goal, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Goal successfully updated"),
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

        A HTTP endpoint that deletes a Goal for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        goal = self.get_goal_object(pk)
        if goal is None:
            return Response(
                response_json(status=False, data=None, message=f"Goal with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            goal.delete()
            return Response(
                response_json(status=True, data=None, message="Goal deleted successfully"), status=status.HTTP_200_OK
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_goal_object(self, pk):
        """Internal method for class GoalView

        A class-level method that returns a Goal Object for provided PK

        Parameters
        ----------
        pk : integer


        Returns
        -------
        apps.goal.models
            returns Goal model object if fetched successfully, reuturns None otherwise
        """
        try:
            goal = Goal.objects.get(pk=pk)
            return goal
        except Goal.DoesNotExist:
            logger.info(f"Goal object with the id: {pk} doesn't exist")
            return None


class GoalsView(APIView):
    """GoalsView class

    This view performs POST and FETCHALL operations for Goal

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

        A HTTP endpoint that returns all Goal objects.
        It is available on both admin and mobile side.

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
                goals = Goal.objects.all()
                serializers = GoalSerializer(goals, many=True)
                return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

            else:
                query_data = (
                    SessionLength.objects.filter(goal__required=True)
                    .values("goal_id", "total_session_length", "goal__name", "goal__gender")
                    .annotate(goal_count=Count("goal_id"), session_length_count=Count("total_session_length"))
                    .filter(goal_count__gte=3, session_length_count__gte=3)
                    .order_by("goal_id")
                )
                valid_objects = []
                response_objects = []
                distinct_goals = []
                for data in query_data:
                    if RepsRange.objects.filter(goal=data["goal_id"]).exists():
                        valid_objects.append(data)
                        distinct_goals.append(data["goal_id"])

                distinct_goals = list(dict.fromkeys(distinct_goals))
                for goal_id in distinct_goals:
                    related_goals = [x for x in valid_objects if x["goal_id"] == goal_id]
                    response_object = {}
                    response_object["goal_id"] = goal_id
                    response_object["goal_name"] = related_goals[0]["goal__name"]
                    response_object["goal_gender"] = related_goals[0]["goal__gender"]
                    total_session_lengths = []
                    for goal_data in related_goals:
                        total_session_lengths.append(goal_data["total_session_length"])
                    response_object["session_lengths"] = total_session_lengths
                    response_objects.append(response_object)

                return Response(response_json(status=True, data=response_objects), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=GoalSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request

        A HTTP endpoint that saves a Goal object  in DB


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

                serializer = GoalSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(status=True, data=None, message="Goal object has saved successfully"),
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
