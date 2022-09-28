from rest_framework import serializers

from apps.body_part.serializers import BodyPartSerializer
from apps.controlled.models import (
    ControlProgram,
    ControlProgramInjury,
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
from apps.equipment.serializers import EquipmentOptionSerializer
from apps.goal.serializers import GoalSerializer
from apps.variance.serializers import VarianceSerializer


class WorkoutFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutFlow
        fields = "__all__"


class SessionLengthSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionLength
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["goal"] = GoalSerializer(instance.goal).data
        response["equipment_option"] = EquipmentOptionSerializer(instance.equipment_option).data
        program_designs = []
        PD_objects = ProgramDesign.objects.filter(sequence_flow__session_length__id=instance.id)
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
        response["program_designs"] = program_designs
        return response


class ProgramDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramDesign
        fields = "__all__"
        # TODO: needs to remove later
        """ fields = [
            "id",
            "day",
            "session_per_week",
            "sequence_flow",
            "body_part_classification",
            "variance",
            "body_part",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["session_per_week"] = SessionSerializer(instance.session_per_week).data
        response["sequence_flow"] = WorkoutFlowSerializer(instance.sequence_flow).data
        response["body_part_classification"] = BodyPartSerializer(instance.body_part_classification).data
        response["variance"] = VarianceSerializer(instance.variance).data
        response["body_part"] = BodyPartSerializer(instance.body_part).data
        del response["body_part"]["classifications"]

        return response """


class PDSwaggerSerializer(serializers.ModelSerializer):
    session_length_id = serializers.IntegerField(write_only=True, required=False)
    workflows = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = ProgramDesign
        fields = ["day", "session_per_week", "session_length_id", "workflows"]


class FirstEverCalcSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirstEverCalc
        fields = "__all__"


class ExerciseRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseRelationship
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["exercise"] = ExerciseSerializer(instance.exercise).data
        del response["exercise"]["created_at"]
        del response["exercise"]["updated_at"]
        return response


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"


class ControlProgramInjurySerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlProgramInjury
        fields = ("injury", "injury_type")

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["injury_name"] = instance.injury.name
        response["injury_type_name"] = instance.injury_type.name
        return response


class ControlProgramSerializer(serializers.ModelSerializer):
    cp_injuries = ControlProgramInjurySerializer(many=True)

    class Meta:
        model = ControlProgram
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["body_part_classification"] = None
        response["variance"] = None
        response["equipment_option"] = EquipmentOptionSerializer(instance.equipment_option).data
        response["body_part"] = BodyPartSerializer(instance.body_part).data
        if instance.body_part_classification_id:
            response["body_part_classification"] = BodyPartSerializer(instance.body_part_classification).data
        if instance.variance_id:
            response["variance"] = VarianceSerializer(instance.variance).data
        response["exercise"] = ExerciseSerializer(instance.exercise).data
        del response["body_part"]["classifications"]
        return response

    def create(self, validated_data):
        cp_injuries = validated_data.pop("cp_injuries")
        control_program = ControlProgram(**validated_data)
        control_program.save()
        for cp_injury in cp_injuries:
            ControlProgramInjury.objects.create(control_program=control_program, **cp_injury)
        return control_program

    def update(self, instance, validated_data):
        cp_injuries = validated_data.pop("cp_injuries")
        ControlProgram.objects.filter(id=instance.id).update(**validated_data)
        ControlProgramInjury.objects.filter(control_program=instance).delete()
        for cp_injury in cp_injuries:
            ControlProgramInjury.objects.create(control_program=instance, **cp_injury)
        return instance


class EquipmentRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentRelation
        fields = "id", "exercise_program"


class EquipmentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentGroup
        fields = "__all__"


class EquipmentCombinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCombination
        fields = "__all__"


class SwaggerEquipmentCombinationSerializer(serializers.ModelSerializer):
    equipment = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = EquipmentCombination
        fields = ["equipment"]


class SwaggerEquipmentRelationSerializer(serializers.ModelSerializer):
    equipment_combination = SwaggerEquipmentCombinationSerializer(many=True)

    class Meta:
        model = EquipmentRelation
        fields = ["exercise_program", "equipment_combination"]


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"


class SwaggerWorkoutFlowSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=250)
    value = serializers.CharField(max_length=250)
    body_part = serializers.IntegerField()
    body_part_classification = serializers.IntegerField()
    variance = serializers.IntegerField()

    class Meta:
        model = WorkoutFlow
        fields = ["name", "value", "body_part", "body_part_classification", "variance"]


class SwaggerProgramDesignSerializer(serializers.ModelSerializer):
    session_per_week = serializers.IntegerField()
    day = serializers.IntegerField()
    workout_flows = SwaggerWorkoutFlowSerializer(many=True)

    class Meta:
        model = ProgramDesign
        fields = ["session_per_week", "day", "workout_flows"]


class SwaggerSessoinLengthSerializer(serializers.ModelSerializer):
    program_designs = SwaggerProgramDesignSerializer(many=True)

    class Meta:
        model = SessionLength
        fields = [
            "total_session_length",
            "equipment_option",
            "goal",
            "total_sets",
            "workout_time",
            "rest_time",
            "warm_up_time",
            "program_designs",
        ]
