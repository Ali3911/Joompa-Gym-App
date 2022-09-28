"""Session serializers file."""
from rest_framework import serializers

from apps.session.models import Session


class SessionSerializer(serializers.ModelSerializer):
    """Serializer class for model Session


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer SessionSerializer"""

        model = Session
        fields = "__all__"
