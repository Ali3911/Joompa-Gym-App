"""BodyPart serializers file."""
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.body_part.models import BodyPart


class ClassificationSerializer(serializers.ModelSerializer):
    """Serializer class for classification in model BodyPart


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer ClassificationSerializer"""

        model = BodyPart
        fields = ("id", "name", "required", "classification", "created_at")


class BodyPartSerializer(serializers.ModelSerializer):
    """Serializer class for model BodyPart


    Parameters
    ----------
    serializers : rest_framework

    """

    name = serializers.CharField(
        max_length=100, validators=[UniqueValidator(queryset=BodyPart.objects.filter(classification=None))]
    )
    classifications = ClassificationSerializer(many=True, required=False)

    class Meta:
        """Meta class for Serializer BodyPartSerializer"""

        model = BodyPart
        fields = fields = ("id", "name", "required", "classifications", "created_at")

    def create(self, validated_data):
        """customized create method for BodyPartSerializer

        Override method to save both classification and bodypart

        Parameters
        ----------
        validated_data : dict


        Returns
        -------
        apps.body_part.models

        """
        classifications = []
        if "classifications" in validated_data.keys():
            classifications = validated_data.pop("classifications")
        body_part = BodyPart.objects.create(**validated_data)
        for classification in classifications:
            BodyPart.objects.create(classification=body_part, **classification)
        return body_part
