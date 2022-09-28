import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.utils import response_json
from apps.variance.serializers import Variance, VarianceSerializer

logger = logging.getLogger(__name__)


class VarianceView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/variances/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """
        :param request: json required only one level, nested json is not allowed.
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """

        variance = self.get_variance_object(pk)
        if variance is None:
            return Response(
                response_json(status=False, data=None, message=f"Variance object with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = VarianceSerializer(variance)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="POST /api/variances/{id}/",
        request_body=VarianceSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """
        :param request: json required only one level, nested json is not allowed.
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        message = "Error occurred while updating the data in the database."
        variance = self.get_variance_object(pk)
        if variance is None:
            return Response(
                response_json(status=False, data=None, message=f"Variance with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = VarianceSerializer(variance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Variance successfully updated"),
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
        operation_description="DELETE /api/variances/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """
        :param request: required delete request
        :param pk: primary key
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        variance = self.get_variance_object(pk)
        if variance is None:
            return Response(
                response_json(status=False, data=None, message=f"Variance with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            variance.delete()
            return Response(
                response_json(status=True, data=None, message="Variance deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="GET /api/variances/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
        },
    )
    def get_variance_object(self, pk):
        """
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return error.
        """
        try:
            variance = Variance.objects.get(pk=pk)
            return variance
        except Variance.DoesNotExist:
            logger.info(f"Variance object with the id: {pk} doesn't exist")
            return None


class VariancesView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/variances/",
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
            variances = Variance.objects.all()
            serializers = VarianceSerializer(variances, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="POST /api/variances/",
        request_body=VarianceSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 400 return errors, if 500 return exception message
        """
        message = "Error occurred while saving the data into the database."
        try:
            serializer = VarianceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=None, message="Variance object has saved successfully"),
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
