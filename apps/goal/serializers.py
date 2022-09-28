"""Goal serializers file."""
from rest_framework import serializers

from apps.goal.models import Goal


class GoalSerializer(serializers.ModelSerializer):
    """Serializer class for model Goal


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer GoalSerializer"""

        model = Goal
        fields = "__all__"
