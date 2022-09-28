import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError, transaction

from apps.body_part.models import BodyPart
from apps.controlled.models import (
    ControlProgram,
    EquipmentCombination,
    EquipmentGroup,
    EquipmentRelation,
    Exercise,
    ExerciseRelationship,
    FirstEverCalc,
    ProgramDesign,
    SessionLength,
    Video,
    WorkoutFlow,
)
from apps.controlled.serializers import (
    ControlProgramSerializer,
    EquipmentRelationSerializer,
    ExerciseRelationshipSerializer,
    ExerciseSerializer,
    FirstEverCalcSerializer,
    PDSwaggerSerializer,
    ProgramDesignSerializer,
    SessionLengthSerializer,
    SwaggerEquipmentCombinationSerializer,
    SwaggerEquipmentRelationSerializer,
    SwaggerSessoinLengthSerializer,
    VideoSerializer,
    WorkoutFlowSerializer,
)
from apps.equipment.models import Equipment
from apps.pagination import CustomPagination
from apps.session.models import Session
from apps.utils import response_json
from apps.variance.models import Variance

logger = logging.getLogger(__name__)


class SessionLengthView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def check_duplication(self, pd, session_lengths_ids):
        for id in session_lengths_ids:
            existing_pds = ProgramDesign.objects.filter(sequence_flow__session_length__id=id)
            if existing_pds.exists():
                for existing_pd in existing_pds:
                    if int(pd["session_per_week"]) == existing_pd.session_per_week_id:
                        body_part_classification = None
                        variance = None

                        if pd["body_part_classification"]:
                            body_part_classification = int(pd["body_part_classification"])

                        if pd["variance"]:
                            variance = int(pd["variance"])
                        if (
                            int(pd["body_part"]) == existing_pd.body_part_id
                            and body_part_classification == existing_pd.body_part_classification_id
                            and variance == existing_pd.variance_id
                            and int(pd["day"]) == existing_pd.day
                        ):
                            raise IntegrityError("Same session length data with day " + str(pd["day"]) + " exists")

    @swagger_auto_schema(
        operation_description="GET /api/sessions-lengths/",
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
            session_lengths = SessionLength.objects.all()
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(session_lengths, request)
            session_length = SessionLengthSerializer(result_page, many=True)
            response_object = paginator.get_paginated_response(data=session_length.data)
            return Response(response_json(status=True, data=response_object, message=None), status=status.HTTP_200_OK)

        except NotFound as e:
            logger.exception(f"{str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="POST /api/session-lengths/",
        request_body=SwaggerSessoinLengthSerializer,
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 400 return errors, if 500 return exception message
        """
        message = "Error occurred while saving the data into the database."
        try:
            with transaction.atomic():
                serializer = SessionLengthSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    session_length_id = serializer.data["id"]
                    prev_session_lengths_data = list(
                        SessionLength.objects.filter(
                            goal=serializer.data["goal"]["id"],
                            equipment_option=serializer.data["equipment_option"]["id"],
                            total_session_length=serializer.data["total_session_length"],
                        )
                    )
                    prev_session_lengths_ids = [x.id for x in prev_session_lengths_data]
                    for pd in request.data["program_designs"]:

                        for workout in pd["workout_flows"]:
                            if "value" in workout:
                                pd["body_part"] = workout["body_part"]
                                pd["body_part_classification"] = workout["body_part_classification"]
                                pd["variance"] = workout["variance"]
                                self.check_duplication(pd, prev_session_lengths_ids)
                            else:
                                pd["body_part"] = ""
                                pd["body_part_classification"] = ""
                                pd["variance"] = ""

                            workout["session_length"] = session_length_id
                            serializer = WorkoutFlowSerializer(data=workout)
                            if serializer.is_valid():
                                serializer.save()
                                workout_id = serializer.data["id"]
                                pd["sequence_flow"] = workout_id
                                serializer = ProgramDesignSerializer(data=pd)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    raise IntegrityError(serializer.errors)
                            else:
                                raise IntegrityError(serializer.errors)

                    return Response(
                        response_json(status=True, data=None, message="Session Length saved successfully."),
                        status=status.HTTP_201_CREATED,
                    )

                else:
                    raise IntegrityError(serializer.errors)

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


class SessionLengthsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/session-length/{id}/",
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
        session_length = self.get_session_length_object(pk)
        if session_length is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Session-length object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            session_length = session_length.to_dict()
            program_designs = []
            PD_objects = ProgramDesign.objects.filter(sequence_flow__session_length__id=pk)
            PD_objects_distinct = PD_objects.values("day").distinct()
            for data in PD_objects_distinct:
                day = data["day"]
                PD_response_object = {}
                PD_response_object["day"] = day
                workout_flows = []
                for PD in PD_objects.filter(day=day):
                    PD_response_object["session_per_week"] = PD.session_per_week.id
                    workout = {}
                    workout["program_design_id"] = PD.id
                    workout["workout_flow_id"] = PD.sequence_flow_id
                    workout["name"] = PD.sequence_flow.name
                    if PD.sequence_flow.value != "":
                        workout["value"] = PD.sequence_flow.value
                    if PD.body_part is not None:
                        workout["body_part"] = PD.body_part.id
                    if PD.body_part_classification is not None:
                        workout["body_part_classification"] = PD.body_part_classification.id
                    if PD.variance is not None:
                        workout["variance"] = PD.variance.id
                    workout_flows.append(workout)

                PD_response_object["workout_flows"] = workout_flows
                program_designs.append(PD_response_object)

            session_length["program_designs"] = program_designs
            return Response(response_json(status=True, data=session_length), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="PUT /api/session-length/{id}/",
        request_body=SwaggerSessoinLengthSerializer,
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
        session_length = self.get_session_length_object(pk)
        if session_length is None:
            return Response(
                response_json(status=False, data=None, message=f"Session-length with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            with transaction.atomic():
                serializer = SessionLengthSerializer(session_length, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    for pd in request.data["program_designs"]:
                        for workout in pd["workout_flows"]:
                            if "value" in workout:
                                pd["body_part"] = workout["body_part"]
                                pd["body_part_classification"] = workout["body_part_classification"]
                                pd["variance"] = workout["variance"]

                            else:
                                pd["body_part"] = ""
                                pd["body_part_classification"] = ""
                                pd["variance"] = ""
                                workout["value"] = ""

                            instance = WorkoutFlow.objects.get(pk=workout["workout_flow_id"])
                            serializer = WorkoutFlowSerializer(instance, data=workout)
                            if serializer.is_valid():
                                serializer.save()
                                pd["sequence_flow"] = workout["workout_flow_id"]
                                instance_PD = ProgramDesign.objects.get(pk=workout["program_design_id"])
                                serializer = ProgramDesignSerializer(instance_PD, data=pd)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    raise IntegrityError(serializer.errors)
                            else:
                                raise IntegrityError(serializer.errors)

                    return Response(
                        response_json(status=True, data=None, message="Session Length updated successfully."),
                        status=status.HTTP_200_OK,
                    )
                else:
                    raise IntegrityError(serializer.errors)

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
        operation_description="DELETE /api/session-length/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """
        :param request: required delete request
        :param pk: primary key
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        session_length = self.get_session_length_object(pk)
        if session_length is None:
            return Response(
                response_json(status=False, data=None, message=f"Session-length with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            session_length.delete()
            return Response(
                response_json(status=True, data=None, message="Session-length deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_session_length_object(self, pk):
        """
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return error.
        """
        try:
            session_length = SessionLength.objects.get(pk=pk)
            return session_length
        except SessionLength.DoesNotExist:
            logger.info(f"Session-length object with the id: {pk} doesn't exist")
            return None


# TODO: needs to remove later
class ProgramDesignsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/program-designs/",
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def get(self, request):

        try:
            program_design_objects = ProgramDesign.objects.all()
            serializer = ProgramDesignSerializer(instance=program_design_objects, many=True)
            response_dict = {}
            for serialized_data in serializer.data:
                seq_objects = []
                session_length_id = serialized_data.get("sequence_flow")["session_length"]
                workout_flow_objects = WorkoutFlow.objects.filter(session_length_id=session_length_id)
                workouts = WorkoutFlowSerializer(workout_flow_objects, many=True)
                for workout in workouts.data:
                    seq_objects.append(workout)
                serialized_data["sequence_flow"] = seq_objects
                if serialized_data.get("day") not in response_dict.keys():
                    response_dict[serialized_data.get("day")] = [serialized_data]
                else:
                    response_dict[serialized_data.get("day")].append(serialized_data)
            return Response(response_json(status=True, data=response_dict), status=status.HTTP_200_OK)
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def __to_pd_objects(self, data):
        program_records = []
        for key, records in data["workflows"].items():
            workflow = WorkoutFlow.objects.filter(value=key, session_length=data["session_length_id"])
            for record in records:
                record["sequence_flow"] = workflow[0].id

                record["session_per_week"] = data["session_per_week"]
                program_records.append(record)
        return program_records

    @swagger_auto_schema(
        operation_description="POST /api/program-designs/",
        request_body=PDSwaggerSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            data = request.data
            program_records = self.__to_pd_objects(data=data)
            serializer = ProgramDesignSerializer(data=program_records, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Program Design saved successfully."),
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

    @swagger_auto_schema(
        operation_description="PUT /api/program-designs/",
        request_body=PDSwaggerSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def put(self, request):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        message = "Error occurred while updating the data in the database."
        try:
            data = request.data
            pd_objects = self.__to_pd_objects(data)
            new_pd_objects = []
            serializer = ProgramDesignSerializer(data=pd_objects, many=True)
            if not serializer.is_valid():
                return Response(
                    response_json(status=False, data=serializer.errors, message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                for record in pd_objects:
                    record["session_per_week"] = Session.objects.get(id=record["session_per_week"])
                    record["sequence_flow"] = WorkoutFlow.objects.get(id=record["sequence_flow"])
                    record["body_part_classification"] = BodyPart.objects.get(id=record["body_part_classification"])
                    record["variance"] = Variance.objects.get(id=record["variance"])
                    record["body_part"] = BodyPart.objects.get(id=record["body_part"])
                    pd_object = None
                    if "id" not in record.keys():
                        pd_object = ProgramDesign(**record)
                        pd_object.save()
                        new_pd_objects.append(pd_object.id)
                    else:
                        pd_object = ProgramDesign.objects.filter(id=record["id"])
                        record.pop("id")
                        pd_object.update(**record)

            except Exception:
                ProgramDesign.objects.filter(id__in=new_pd_objects).delete()
                return Response(
                    response_json(status=False, data=None, message=message), status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                response_json(status=True, data=None, message="Program Design updated " "successfully."),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# TODO: needs to remove later
class ProgramDesignView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/program-design/{id}/",
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request, session_length_id):
        """
        :param request: json required only one level, nested json is not allowed.
        :param session_length_id: session_length_id required by url
        :return: if 200 return data, if 404 return Not Found, if 500 return server error
        """

        workout_flow_objects = WorkoutFlow.objects.filter(session_length_id=session_length_id).values_list("id")
        if workout_flow_objects is None:
            return Response(
                response_json(
                    status=False,
                    data=None,
                    message=f"Session Lenght object with the id: {session_length_id} doesn't exist",
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            pd_object = ProgramDesign.objects.filter(sequence_flow__in=list(workout_flow_objects))
            serializer = ProgramDesignSerializer(pd_object, many=True)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_program_design_object(self, pk):
        """
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return error.
        """
        try:
            program_design = ProgramDesign.objects.get(pk=pk)
            return program_design
        except ProgramDesign.DoesNotExist:
            logger.info(f"Program Design object with the id: {pk} doesn't exist")
            return None


class FirstEverCalcsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="POST /api/first-ever-calcs/",
        request_body=FirstEverCalcSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            data = request.data
            serializer = FirstEverCalcSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="FirstEverCalc saved successfully."),
                    status=status.HTTP_201_CREATED,
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
        operation_description="GET /api/first-ever-calcs/",
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
            firstevercalc_data = FirstEverCalc.objects.all()
            serializers = FirstEverCalcSerializer(firstevercalc_data, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FirstEverCalcView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/first-ever-calc/{id}/",
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

        firstevercal_objects = self.get_object(control_program=pk)
        if firstevercal_objects.count() == 0:
            return Response(
                response_json(
                    status=False, data=None, message=f"Firstevercalc with the program id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = FirstEverCalcSerializer(firstevercal_objects, many=True)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="PUT /api/first-ever-calc/{id}/",
        request_body=FirstEverCalcSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
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
        firstevercalc = self.get_object(pk)
        if firstevercalc is None:
            return Response(
                response_json(status=False, data=None, message=f"Firstevercalc with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = FirstEverCalcSerializer(firstevercalc, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Firstevercalc successfully updated"),
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
        operation_description="DELETE /api/first-ever-calc/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        """
        :param request: required delete request
        :param pk: primary key
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        firstevercalc = self.get_object(pk)
        if firstevercalc is None:
            return Response(
                response_json(status=False, data=None, message=f"Firstevercalc with the id: {pk} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            firstevercalc.delete()
            return Response(
                response_json(status=True, data=None, message="Firstevercalc deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk=None, control_program=None):
        firstevercal_data = None
        try:
            if pk:
                firstevercal_data = FirstEverCalc.objects.get(pk=pk)
            if control_program:
                firstevercal_data = FirstEverCalc.objects.filter(control_program=control_program)
        except FirstEverCalc.DoesNotExist:
            logger.info(f"Firstevercalc object with the id: {pk} doesn't exist")
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}:  {str(e)}")

        return firstevercal_data


class ControlProgramView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/control-program/{id}/",
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request, pk):
        """
        :param request: json required only one level, nested json is not allowed.
        :param pk: pk required by url
        :return: if 200 return data, if 404 return Not Found, if 500 return server error
        """

        control_program_object = self.get_object(pk=pk)
        if control_program_object is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Control Program object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = ControlProgramSerializer(control_program_object)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="PUT /api/control-program/{id}",
        request_body=ControlProgramSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def put(self, request, pk):
        """
        :param pk: primary key required by url
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        message = "Error occurred while updating the data in the database."
        control_program_object = self.get_object(pk=pk)
        if control_program_object is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Control Program object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            data = request.data
            exercise_name = data.pop("exercise")
            Exercise.objects.filter(id=control_program_object.exercise.id).update(name=exercise_name)
            data["exercise"] = control_program_object.exercise.id
            serializer = ControlProgramSerializer(control_program_object, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(
                        status=True, data=serializer.data, message="Control Program updated " "successfully."
                    ),
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    response_json(status=False, data=serializer.errors, message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(
                    status=False, data=None, message=e.args[0].split("DETAIL:")[1].replace('\n"', "").strip()
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="DELETE /api/control-program/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, pk):
        control_program_object = self.get_object(pk)
        if control_program_object is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Control Program Object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            control_program_object.exercise.delete()
            control_program_object.delete()
            return Response(
                response_json(status=True, data=None, message="Control Program deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, pk):
        """
        :param pk: primary key required by url
        :return: if 200 return data, if 400 return error.
        """
        try:
            control_program = ControlProgram.objects.get(pk=pk)
            return control_program
        except ControlProgram.DoesNotExist:
            logger.info(f"Control Program object with the id: {pk} doesn't exist")
            return None


class ControlProgramsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_description="GET /api/control-programs/",
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request):

        try:
            control_program_objects = ControlProgram.objects.all()
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(control_program_objects, request)
            serializer = ControlProgramSerializer(result_page, many=True)
            response_object = paginator.get_paginated_response(data=serializer.data)
            return Response(response_json(status=True, data=response_object, message=None), status=status.HTTP_200_OK)
        except NotFound as e:
            logger.exception(f"{str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}: {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="POST /api/control-programs/",
        request_body=ControlProgramSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            with transaction.atomic():
                data = request.data
                exercise_name = data.pop("exercise")
                if Exercise.objects.filter(name=exercise_name).exists():
                    return Response(
                        response_json(status=False, data=None, message=f"Exercise {exercise_name} already exist"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                exercise = Exercise.objects.create(name=exercise_name)
                data["exercise"] = exercise.id
                serializer = ControlProgramSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        response_json(
                            status=True, data=serializer.data, message="Program Design saved " "successfully."
                        ),
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    raise IntegrityError(serializer.errors)

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


class ExercisesView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/exercises/",
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
            exercises = Exercise.objects.all()
            serializers = ExerciseSerializer(exercises, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExerciseRelationshipView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/exercise-relationship/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def get(self, request, id):
        """
        :param request: json required only one level, nested json is not allowed.
        :param id: control_program_id required by url
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        # param id is control_program_id
        exercise_relationship = self.get_object(id)
        if exercise_relationship.count() == 0:
            return Response(
                response_json(
                    status=False,
                    data=None,
                    message=f"Exercise_relationships for the control program id: {id} doesn't exist",
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = ExerciseRelationshipSerializer(exercise_relationship, many=True)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="PUT /api/exercise-relationship/{id}/",
        request_body=ExerciseRelationshipSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def put(self, request, id):
        """
        :param request: json required only one level, nested json is not allowed.
        :param id: control_program_id required by url
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        # param id is exercise_relationship_id
        message = "Error occurred while updating the data in the database."
        try:
            exercise_relationship = ExerciseRelationship.objects.get(pk=id)
        except ExerciseRelationship.DoesNotExist:
            return Response(
                response_json(
                    status=False, data=None, message=f"Exercise_relationship with the id: {id} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = ExerciseRelationshipSerializer(exercise_relationship, data=request.data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(
                    response_json(status=False, data=serializer.errors, message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                response_json(status=True, data=None, message="Exercise Relationship updated successfully."),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="DELETE /api/exercise-relationship/{id}/",
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, id):
        """
        :param request: required delete request
        :param id: primary key of Exercise Relationship
        :return: if 200 return data, if 400 return errors, if 500 return server error
        """
        try:
            exercise_relationship = ExerciseRelationship.objects.get(pk=id)
        except ExerciseRelationship.DoesNotExist:
            return Response(
                response_json(
                    status=False, data=None, message=f"Exercise_relationship with the id: {id} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            exercise_relationship.delete()
            return Response(
                response_json(status=True, data=None, message="Exercise_relationship deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, control_program_id):
        try:
            exercise_relationship_data = ExerciseRelationship.objects.filter(control_program=control_program_id)
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}: {str(e)}")
        else:
            return exercise_relationship_data


class ExerciseRelationshipsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="POST /api/exercise-relationships/",
        request_body=ExerciseRelationshipSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            data = request.data
            serializer = ExerciseRelationshipSerializer(data=data, many=True)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(
                        status=True, data=serializer.data, message="Exercise Relationship saved successfully."
                    ),
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

    @swagger_auto_schema(
        operation_description="GET /api/exercise-relationships/",
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
            exercise_relationships = ExerciseRelationship.objects.all()
            serializers = ExerciseRelationshipSerializer(exercise_relationships, many=True)
            return Response(response_json(status=True, data=serializers.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EquipmentRelationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="GET /api/equipment-relation/{cp_id}",
        responses={200: "OK", 500: "Internal Server Error", 404: "Not Found"},
    )
    def get(self, request, cp_id):
        """
        :param request: json required only one level, nested json is not allowed.
        :return: if 200 return data, if 404 return errors, if 500 return server error
        """

        equipment_relations = EquipmentRelation.objects.filter(exercise_program=cp_id)

        if equipment_relations.count() == 0:
            return Response(
                response_json(
                    status=False,
                    data=None,
                    message=f"Equipment Relation object with the control program id: {cp_id} doesn't exist",
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            response_data = {}
            response_data["exercise_program"] = cp_id
            equipment_combinations = []
            for data in equipment_relations:
                combo = data.equipment_combination.to_dict()
                equipment_groups = data.equipment_combination.equipment_combination_groups.all()
                groups = []
                for equipment_group in equipment_groups:
                    groups.append(equipment_group.to_dict())
                combo["equipment_groups"] = groups
                equipment_combinations.append(combo)
            response_data["equipment_combination"] = equipment_combinations
            return Response(response_json(status=True, data=response_data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="DELETE /api/equipment-relation/{cp_id}/",
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, cp_id):
        """
        :param request: required delete request
        :param pk: primary key
        :return: if 200 return data,if 500 return server error
        """

        try:
            equipment_relations = EquipmentRelation.objects.filter(exercise_program=cp_id)

            if len(equipment_relations) == 0:
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=f"Equipment Relation object with the control program id: {cp_id} doesn't exist",
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )

            for data in equipment_relations:
                equipment_combination = EquipmentCombination.objects.get(pk=data.equipment_combination_id)
                equipment_combination.delete()

            return Response(
                response_json(status=True, data=None, message="Equipment_relation deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EquipmentCombinationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="PUT /api/equipment-combination/{id}",
        request_body=SwaggerEquipmentCombinationSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def put(self, request, pk):
        """
        pk: ID of EquipmentCombination
        Request JSON Format:
           {
            "equipment":[1,2,3]
           }
        """
        message = "Error occurred while updating the data into the database."
        equipment_combination_object = self.get_equipment_combination_object(pk)
        if equipment_combination_object is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Equipment Combination object with the id: {pk} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            data = request.data
            equipment_relation = EquipmentRelation.objects.get(equipment_combination=pk)
            equipments = list(dict.fromkeys(data["equipment"]))
            equipments.sort()
            equipment_relations = EquipmentRelation.objects.filter(
                exercise_program=equipment_relation.exercise_program
            )
            for equipment_relation in equipment_relations:
                equipment_groups = EquipmentGroup.objects.filter(
                    equipment_combination=equipment_relation.equipment_combination
                )
                equipments_list = [x.equipment.id for x in equipment_groups]
                equipments_list.sort()
                if equipments == equipments_list:
                    return Response(
                        response_json(
                            status=False,
                            data=equipments,
                            message="Equipment Relation with this combination alreay exists",
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            equipment_groups = EquipmentGroup.objects.filter(equipment_combination=pk)
            equipment_groups.delete()
            for equipment_id in equipments:
                equipment_object = Equipment.objects.get(pk=equipment_id)
                EquipmentGroup.objects.create(
                    equipment_combination=equipment_combination_object, equipment=equipment_object
                )

            return Response(
                response_json(status=True, data=None, message="Equipment Combination updated successfully."),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="DELETE /api/equipment-combination/{id}",
        responses={200: "OK", 500: "Internal Server Error", 404: "Not Found"},
    )
    def delete(self, request, pk):
        """
        :param request: required delete request
        :param pk: primary key
        :return: if 200 return data,if 500 return server error, if 404 data not found
        """

        try:
            equipment_combination = self.get_equipment_combination_object(pk)
            if equipment_combination is None:
                return Response(
                    response_json(
                        status=False, data=None, message=f"Equipment Combination object with id: {pk} doesn't exist"
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )

            equipment_combination.delete()
            return Response(
                response_json(status=True, data=None, message="Equipment Combination deleted successfully"),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            message = "Error occurred while deleting the data from the database"
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_equipment_combination_object(self, pk):

        try:
            equipment_combination = EquipmentCombination.objects.get(pk=pk)
            return equipment_combination
        except EquipmentCombination.DoesNotExist:
            logger.info(f"Equipment Combination object with the id: {pk} doesn't exist")
            return None


class EquipmentRelationsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="POST /api/equipment-relations/",
        request_body=SwaggerEquipmentRelationSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            serializer = EquipmentRelationSerializer(data=request.data)
            if serializer.is_valid():
                data = request.data

                equipment_request_data = data["equipment_combination"]
                equipment_groups_request_data = []
                for equipment in equipment_request_data:
                    equipment_list = equipment["equipment"]
                    equipment_list.sort()
                    equipment_groups_request_data.append(equipment_list)
                equipment_relations = EquipmentRelation.objects.filter(exercise_program=data["exercise_program"])
                for equipment_relation in equipment_relations:
                    equipment_groups = EquipmentGroup.objects.filter(
                        equipment_combination=equipment_relation.equipment_combination
                    )
                    equipments = [x.equipment.id for x in equipment_groups]
                    equipments.sort()
                    if equipments in equipment_groups_request_data:
                        return Response(
                            response_json(
                                status=False,
                                data=equipments,
                                message="Equipment Relation with this combination alreay exists",
                            ),
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                combination_name_counter = 1
                cp = ControlProgram.objects.get(pk=data["exercise_program"])
                for equipment in data["equipment_combination"]:
                    equipment_combination = EquipmentCombination.objects.create(
                        name="combination " + str(combination_name_counter)
                    )
                    _ = EquipmentRelation.objects.create(
                        equipment_combination=equipment_combination, exercise_program=cp
                    )
                    for equipment_id in equipment["equipment"]:
                        equipment_object = Equipment.objects.get(pk=equipment_id)
                        EquipmentGroup.objects.create(
                            equipment_combination=equipment_combination, equipment=equipment_object
                        )
                    combination_name_counter = combination_name_counter + 1
                return Response(
                    response_json(status=True, data=None, message="Equipment Relation saved successfully."),
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


class VideosView(APIView):
    """VideoView class

    This view performs POST operations for Video

    Parameters
    ----------
    APIView : rest_framework.views

    """

    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        request_body=VideoSerializer,
        responses={201: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def post(self, request):
        message = "Error occurred while saving the data into the database."
        try:
            data = request.data
            serializer = VideoSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Video saved successfully."),
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


class VideoView(APIView):
    """VideoView class

    This view performs GET,PUT and DELETE operations for Video

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
    def get(self, request, id):
        """HTTP GET request

        A HTTP endpoint that returns VideoView object for provided control_program_id

        Parameters
        ----------
        request : django.http.request

        id : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """
        # param id is control_program_id
        video = self.get_object(id)
        if video is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Video for the control program id: {id} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = VideoSerializer(video, many=True)
            return Response(response_json(status=True, data=serializer.data), status=status.HTTP_200_OK)

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=VideoSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
        },
    )
    def put(self, request, id):

        """HTTP PUT request

        A HTTP endpoint that updates a VideoView object for provided PK

        Parameters
        ----------
        request : django.http.request

        id : integer


        Returns
        -------
        rest_framework.response
            returns success message if data updated successfully,error message otherwise
        """
        # param id is video_id
        message = "Error occurred while updating the data in the database."
        video = Video.objects.get(pk=id)
        if video is None:
            return Response(
                response_json(
                    status=False, data=None, message=f"Video for the control program id: {id} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            serializer = VideoSerializer(video, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    response_json(status=True, data=serializer.data, message="Video successfully updated"),
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
    def delete(self, request, id):
        """HTTP DELETE request

        A HTTP endpoint that deletes a VideoView object for provided PK

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns success message if data deleted successfully,error message otherwise
        """
        video = Video.objects.get(pk=id)
        if video is None:
            return Response(
                response_json(status=False, data=None, message=f"Video with the id: {id} doesn't exist"),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            video.delete()
            return Response(
                response_json(status=True, data=None, message="Video deleted successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            message = "Error occurred while deleting the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_object(self, control_program_id):
        """Internal method for class VideoView

        A class-level method that returns a VideoView Object for provided control_program_id

        Parameters
        ----------
        control_program_id : integer


        Returns
        -------
        apps.controlled.models
            returns Video model object if fetched successfully, returns None otherwise
        """
        try:
            video = Video.objects.filter(control_program=control_program_id)
        except Exception as e:
            message = "Error occurred while fetching the data from the database"
            logger.exception(f"{message}: {str(e)}")
        else:
            return video
