"""Reps in Reserve views file."""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goal.models import Goal
from apps.reps_in_reserve.models import RepsInReserve, RepsRange, RepsRating
from apps.reps_in_reserve.serializers import (
    CustomeRepsInReserveSerializer,
    RepsInReserveSerializer,
    RepsRangeSerializer,
)
from apps.utils import response_json

logger = logging.getLogger(__name__)


class RepsInReserveView(APIView):
    """RepsInReserveView class

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
        """HTTP get request.

        A HTTP api endpoint that get single RepsInReserve object against PK from database.

        Parameters
        ----------
        request : django.http.request
        pk : primary key

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for single RepsInReserve object, error message otherwise
        """
        reps_in_reserve = self.get_object(pk)
        if reps_in_reserve is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"RepsInReserve object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = RepsInReserveSerializer(reps_in_reserve)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=CustomeRepsInReserveSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """HTTP put request

        A HTTP api endpoint that update single RepsInReserve against PK from database.

        ```
        Request body format:
        {
        "fitness_level":67,
        "goal":4,
        "weeks": [
                    {"week":"week1", "value":34}
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
        message = "Error occurred while updating the data in the database."
        reps_in_reserve = self.get_object(pk)
        if reps_in_reserve is None:
            return Response(
                response_json(status=False, data=None, message=f"RepsInReserve with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = RepsInReserveSerializer(reps_in_reserve, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="RepsInReserve successfully updated"),
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
        """HTTP delete request

        A HTTP api endpoint that delete single RepsInReserve against PK from database.

        Parameters
        ----------
        request : django.http.request
        pk : primary key

        Returns
        -------
        rest_framework.response.Response
            returns success message if data deleted successfully in db, error message otherwise
        """
        reps_in_reserve = self.get_object(pk)
        if reps_in_reserve is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"RepsInReserve object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            reps_in_reserve.delete()
            return Response(
                response_json(status=True, data=None, message="RepsInReserve deleted successfully"),
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
            reps_in_reserve = RepsInReserve.objects.get(pk=pk)
            return reps_in_reserve
        except RepsInReserve.DoesNotExist:
            logger.info(f"RepsInReserve object with the id: {pk} doesn't exist")
            return None


class RepsInReservesView(APIView):
    """RepsInReservesView class

    Parameters
    ----------
    APIView : rest_framework.views
    """

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP get request.

        A HTTP api endpoint that get all RepsInReserve objects from database.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for all RepsInReserve objects, error message otherwise
        """
        try:
            reps_in_reserves = RepsInReserve.objects.all()
            serializers = RepsInReserveSerializer(reps_in_reserves, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=CustomeRepsInReserveSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request.

        Save RepsInReserve along with feedback ranges and feedback values
        ```
        Request body format:
        {
        "fitness_level":2,
        "goal":4,
        "weeks": [
                {"week":"week1", "value":34}
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
        message = "Error occurred while saving the data into the database"
        try:
            serializer = RepsInReserveSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=None, message="RepsInReserve successfully inserted."),
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


class RepsConfigurationsView(APIView):
    """RepsConfigurationsView class

    Parameters
    ----------
    APIView : rest_framework.views
    """

    permission_classes = [permissions.IsAdminUser]

    def __get_serialized_data(self, serialized_data):
        """__get_serialized_data function

        A custom function which removes unneccessaary data from dict.

        Parameters
        ----------
        serialized_data : dict

        Returns
        -------
        structured dict
        """
        serialized_data["ratings"] = serialized_data.get("reps_ranges")
        del serialized_data["range_name"]
        del serialized_data["reps_ranges"]
        del serialized_data["goal"]
        return serialized_data

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """HTTP get request.

        A HTTP api endpoint that get all RepsConfiguration objects from database.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for all RepsConfiguration objects, error message otherwise
        """
        try:
            response_list = []
            goals = Goal.objects.all()
            for goal in goals:
                data = {}
                range_names = {}
                data["goal_id"] = goal.id
                data["goal_name"] = goal.name
                rep_ranges = RepsRange.objects.filter(goal=goal)
                for rep_range in rep_ranges:
                    rep_range_obj = {
                        "id": rep_range.id,
                        "value": rep_range.value,
                        "ratings": [rating.to_dict() for rating in rep_range.reps_ranges.all()],
                    }
                    if rep_range.range_name not in range_names:
                        range_names[rep_range.range_name] = [rep_range_obj]
                    else:
                        range_names[rep_range.range_name].append(rep_range_obj)
                data["ranges_count"] = len(range_names.keys())
                data["rep_ranges"] = range_names
                response_list.append(data)

            return Response(response_json(status=True, data=response_list), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logging.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=RepsRangeSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """HTTP POST request.

        Save RepsInReserve along with feedback ranges and feedback values

        ```
        Request body format:
        [
            {
                "goal": 64,
                "value": 6,
                "range_name": "A2",
                "reps_ranges": [
                    {
                        "weight": 30,
                        "reps": 0,
                        "rating": 2
                    }
                ]
            }
        ]
        ```

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if data saves successfully in db, error message otherwise
        """
        message = "Error occurred while saving the data into the database"
        try:
            data = request.data
            serializer = RepsRangeSerializer(data=data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=None, message="RepsRange successfully inserted."),
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


class RepsConfigurationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        request_body=RepsRangeSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def put(self, request, goal_id):
        """HTTP put request

        A HTTP api endpoint that update single RepsRange against goal_id from database.

        ```
        Request body format:
        [
            {
                "goal": 64,
                "value": 6,
                "range_name": "A2",
                "reps_ranges": [
                    {
                        "weight": 30,
                        "reps": 0,
                        "rating": 2
                    }
                ]
            }
        ]
        ```
        Parameters
        ----------
        request : django.http.request
        goal_id : goal_id

        Returns
        -------
        rest_framework.response.Response
            returns success message if data updated successfully in db, error message otherwise
        """
        message = "Error occurred while saving the data into the database"
        reps_ranges_data = self.get_objects(goal_id)
        valid_serializers = []

        if reps_ranges_data.count() == 0:
            return Response(
                response_json(status=False, data=None, message=f"RepsRange with goal id: {goal_id} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            request_data = request.data
            for data in request_data:
                instance = reps_ranges_data.filter(pk=data["id"]).first()
                serializer = RepsRangeSerializer(instance, data=data)
                if serializer.is_valid():
                    valid_serializers.append(serializer)
                else:
                    return Response(
                        response_json(status=False, data=serializer.errors, message=message),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            for serializer in valid_serializers:
                serializer.save()

            return Response(
                response_json(status=True, data=None, message="RepsRange successfully updated."),
                status=status.HTTP_200_OK,
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
    def delete(self, request, goal_id):
        """HTTP delete request

        A HTTP api endpoint that delete single RepsRange against goal_id from database.

        Parameters
        ----------
        request : django.http.request
        goal_id : goal_id

        Returns
        -------
        rest_framework.response.Response
            returns success message if data deleted successfully in db, error message otherwise
        """
        reps_ranges_data = self.get_objects(goal_id)
        if reps_ranges_data.count() == 0:
            return Response(
                response_json(status=False, data=None, message=f"RepsRange with goal id: {goal_id} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            reps_ranges_data.delete()
            return Response(
                response_json(status=True, data=None, message="RepsRange deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
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
    def get(self, request, goal_id):
        """HTTP get request

        A HTTP api endpoint that get single RepsInReserve object against goal_id from database.

        Parameters
        ----------
        request : django.http.request
        goal_id : goal_id

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for single RepsInReserve object, error message otherwise
        """
        reps_ranges_data = self.get_objects(goal_id)
        if reps_ranges_data.count() == 0:
            return Response(
                response_json(status=False, data=None, message=f"RepsRange with goal id: {goal_id} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            response_dict = {}
            serializer = RepsRangeSerializer(reps_ranges_data, many=True)
            serialized_data = serializer.data
            response_dict["goal_id"] = serialized_data[0].get("goal")["id"]
            response_dict["goal_name"] = serialized_data[0].get("goal")["name"]
            response_dict["rep_ranges"] = []
            for serialize_data in serialized_data:
                rep_ranges_dict = {"range_name": serialize_data.get("range_name"), "range_values": []}
                range_values_dict = {
                    "id": serialize_data.get("id"),
                    "value": serialize_data.get("value"),
                    "ratings": [],
                }
                reps_range_name = RepsRating.objects.filter(reps_range_id=serialize_data.get("id"))
                for reps_range in reps_range_name:
                    rating_dict = {
                        "id": reps_range.id,
                        "weight": reps_range.weight,
                        "reps": reps_range.reps,
                        "rating": reps_range.rating,
                    }
                    range_values_dict["ratings"].append(rating_dict)
                rep_ranges_dict["range_values"].append(range_values_dict)
                response_dict["rep_ranges"].append(rep_ranges_dict)
            return Response(response_json(status=True, data=response_dict), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logging.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_objects(self, goal_id):
        """get_object function

        Parameters
        ----------
        goal_id : goal_id

        Returns
        -------
        model object
            return model object against goal_id from database.
        """
        try:
            reps_range = RepsRange.objects.filter(goal=goal_id)
            return reps_range
        except Exception as e:
            logger.info(e)
