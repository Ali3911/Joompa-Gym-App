import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError, transaction

from apps.equipment.models import Equipment, EquipmentOption
from apps.equipment.serializers import CustomeEquipmentSerializer, EquipmentOptionSerializer, EquipmentSerializer
from apps.equipment.validators import check_s3_bucket_access
from apps.utils import response_json

logger = logging.getLogger(__name__)


class EquipmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="GET /api/equipments/",
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 500 return exception message
        """
        try:
            parents = Equipment.objects.filter(level_id=None)
            parents = EquipmentSerializer(parents, many=True).data
            for parent in parents:
                children = Equipment.objects.filter(level_id=parent["id"])
                parent["types"] = EquipmentSerializer(children, many=True).data
            return Response(response_json(status=True, data=parents, message=None), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="POST /api/equipments/",
        request_body=CustomeEquipmentSerializer,
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 400 return errors, if 500 return exception message
        """
        message = "Error occurred while saving the data into the database"
        try:
            with transaction.atomic():
                if request.user.is_staff:

                    if not check_s3_bucket_access():
                        message = "S3 bucket not configured"
                        logger.exception(f"{message}")
                        return Response(
                            response_json(status=False, data=None, message=message),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    types = None
                    data = request.data
                    if "types" in data.keys():
                        types = eval(data["types"])
                        del data["types"]
                    if "image" not in data.keys() and data["level_id"] is None:
                        message = "Image is required"
                        logger.exception(f"{message}")
                        return Response(
                            response_json(status=False, data=None, message=message),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    equipment_serializer = EquipmentSerializer(data=data)
                    if equipment_serializer.is_valid():
                        equipment_serializer.save()
                        # for swagger documentation only
                        if types is not None and len(types) != 0 and types != [{}]:
                            for record in types:
                                record["level_id"] = equipment_serializer.data["id"]
                                serializer = EquipmentSerializer(data=record)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    Equipment.objects.filter(id=equipment_serializer.data["id"]).delete()
                                    return Response(
                                        response_json(status=False, data=serializer.errors, message=message),
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                        return Response(
                            response_json(status=True, data=None, message="Equipment successfully inserted."),
                            status=status.HTTP_201_CREATED,
                        )
                    else:
                        raise IntegrityError(equipment_serializer.errors)
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
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EquipmentView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/equipment/{id}/",
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """
        :param request: json required only one level, nested json is not allowed.
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return errors, if 500 return exception message
        """
        parent_equipment = self.get_object(pk)
        if parent_equipment is None:
            return Response(
                response_json(status=False, data=None, message=f"Equipment object with id {pk} doesn't exist."),
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            parent = EquipmentSerializer(parent_equipment).data
            children = Equipment.objects.filter(level_id=parent["id"])
            parent["types"] = EquipmentSerializer(children, many=True).data
            return Response(response_json(status=True, data=parent, message=None), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="PUT /api/equipment/{id}/",
        request_body=EquipmentSerializer,
        responses={
            400: "Bad Request",
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """
        :param request: json required only one level, nested json is not allowed.
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return errors, if 500 return exception message
        """
        message = "Error occurred while updating the data in the database."
        equipment = self.get_object(pk)
        if equipment is None:
            return Response(
                response_json(status=False, data=None, message=f"Equipment object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = EquipmentSerializer(equipment, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Equipment successfully updated"),
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
        operation_description="DELETE /api/equipment/{id}/",
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """
        :param request: required delete request
        :param pk: primary key
        :return: return 200 if ok else return 500 in case of internal error
        """
        try:
            equipment_object = self.get_object(pk=pk)
            if equipment_object is None:
                return Response(
                    response_json(status=False, data=None, message=f"Equipment with the id: {pk} doesn't exist"),
                    status=status.HTTP_404_NOT_FOUND,
                )
            equipment_object.delete()
            return Response(
                response_json(status=True, data=None, message="Equipment deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="GET /api/equipment/{id}/",
        request_body=EquipmentSerializer,
        responses={
            200: "OK",
        },
    )
    def get_object(self, pk):
        """
        :param pk: primary key required by url
        :return: if 200 return data
        """
        try:
            return Equipment.objects.get(pk=pk)
        except Equipment.DoesNotExist:
            logger.info(f"Equipment object with the id: {pk} doesn't exist")
            return None


class EquipmentOptionsView(APIView):
    """EquipmentOptionsView class

    This view performs FETCHALL operation to fetch the data from the database for EquipmentOptions.
    It will be available on both admin and mobile side.

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

        A HTTP endpoint that returns all EquipmentOptions objects.
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
            equipment_options = EquipmentOption.objects.all()
            serializers = EquipmentOptionSerializer(equipment_options, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
