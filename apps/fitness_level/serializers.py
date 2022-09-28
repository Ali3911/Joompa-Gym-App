"""FitnessLevel serializers file."""
from rest_framework import serializers

from apps.fitness_level.models import FitnessLevel


class FitnessLevelSerializer(serializers.ModelSerializer):
    """Serializer class for model FitnessLevel


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer FitnessLevelSerializer"""

        model = FitnessLevel
        fields = "__all__"
