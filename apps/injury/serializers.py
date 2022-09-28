"""Injury serializers file."""
from rest_framework import serializers

from apps.body_part.serializers import BodyPartSerializer
from apps.injury.models import Injury, InjuryType


class InjuryTypeSerializer(serializers.ModelSerializer):
    """Serializer class for model InjuryType


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer InjuryTypeSerializer"""

        model = InjuryType
        fields = "__all__"


class InjurySerializer(serializers.ModelSerializer):
    """Serializer class for model Injury


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer InjurySerializer"""

        model = Injury
        fields = "__all__"

    def to_representation(self, instance):
        """customized to_representation method for class InjurySerializer

        Override method to include InjuryType data in response JSON

        Parameters
        ----------
        instance : apps.injury.models


        Returns
        -------
        dict
            returns dict object which will be included in response of API
        """
        response = super().to_representation(instance)
        response["body_part"] = BodyPartSerializer(instance.body_part).data
        response["injury_type"] = InjuryTypeSerializer(instance.injury_type).data
        del response["body_part"]["classifications"]
        return response
