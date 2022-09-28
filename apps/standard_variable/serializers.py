"""StandaradVariable serializers file."""
from rest_framework import serializers

from apps.standard_variable.models import StandardVariable


class StandaradVariableSerializer(serializers.ModelSerializer):
    """Serializer class for model StandardVariable


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer StandaradVariableSerializer"""

        model = StandardVariable
        fields = "__all__"
