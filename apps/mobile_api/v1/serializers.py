"""Mobile API serializers file."""
from rest_framework import serializers

from apps.equipment.serializers import EquipmentSerializer
from apps.fitness_level.serializers import FitnessLevelSerializer
from apps.mobile_api.v1.models import (
    UserEquipment,
    UserFeedback,
    UserInjury,
    UserProfile,
    UserProgramDesign,
    UserStandardVariable,
)


class UserProfileSerializer(serializers.ModelSerializer):
    """UserProfileSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    class Meta:
        model = UserProfile
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["fitness_level"] = FitnessLevelSerializer(instance.fitness_level).data["fitness_level"]
        return response


class SwaggerUserProfileSerializer(serializers.ModelSerializer):
    """UserProfileSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    baseline_assessment = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
    equipments = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
    standard_variables = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
    equipment_exist = serializers.BooleanField(write_only=True, required=False, default="yes")

    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = ["user_id"]


class UserStandardVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStandardVariable
        fields = "__all__"


class UserInjurySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInjury
        fields = "__all__"


class UserEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEquipment
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["equipment"] = EquipmentSerializer(instance.equipment).data
        return response


class UserProgramDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgramDesign
        fields = "__all__"


class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = "__all__"


class SwaggerUserFeedbackSerializer(serializers.ModelSerializer):
    """UserFeedbackSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    email = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserFeedback
        fields = ["value", "feedback", "user_program_design", "email"]
        read_only_fields = ["user_profile"]


class UserProgramDesignSwaggerSerializer(serializers.ModelSerializer):
    """UserProgramDesignSwaggerSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    session = serializers.CharField()
    user_program_design_id = serializers.IntegerField()
    user_rir = serializers.IntegerField()
    system_rir = serializers.IntegerField()
    exercise_id = serializers.IntegerField()
    user_rir = serializers.IntegerField()
    system_calculated_reps = serializers.IntegerField()
    system_calculated_weight = serializers.IntegerField()

    class Meta:
        model = UserProgramDesign
        fields = [
            "session",
            "user_program_design_id",
            "user_rir",
            "system_rir",
            "exercise_id",
            "user_rir",
            "system_calculated_reps",
            "system_calculated_weight",
        ]


class UserWorkoutProgramSerializer(serializers.Serializer):
    is_personalized = serializers.BooleanField(required=True)
    goal = serializers.IntegerField(required=False, min_value=1, default=0)
    total_session_length = serializers.IntegerField(required=False, min_value=1, default=0)
    session_per_week = serializers.IntegerField(required=False, min_value=1, default=0)
