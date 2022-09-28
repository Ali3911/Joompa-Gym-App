"""BaselineAssessment serializers file."""
from rest_framework import serializers

from apps.baseline_assessment.models import BaselineAssessment


class BaselineAssessmentSerializer(serializers.ModelSerializer):
    """Serializer class for model BaselineAssessment


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer BaselineAssessmentSerializer"""

        model = BaselineAssessment
        fields = "__all__"
