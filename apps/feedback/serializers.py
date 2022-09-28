"""Feedback serializers file."""
from rest_framework import serializers

from apps.feedback.models import Feedback, FeedbackRange, FeedbackValue


class FeedbackValueSerializer(serializers.ModelSerializer):
    """FeedbackValueSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    class Meta:
        model = FeedbackValue
        fields = ["id", "description", "value", "created_at"]


class FeedbackRangeSerializer(serializers.ModelSerializer):
    """FeedbackRangeSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    class Meta:
        model = FeedbackRange
        fields = ["id", "name", "rir", "range_lower_limit", "range_upper_limit", "created_at"]


class FeedbackSerializer(serializers.ModelSerializer):
    """FeedbackSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    fv_feedbacks = FeedbackValueSerializer(many=True)
    fr_feedbacks = FeedbackRangeSerializer(many=True, required=False)

    class Meta:
        model = Feedback
        fields = ["id", "name", "fr_feedbacks", "fv_feedbacks", "created_at", "type"]

    def create(self, validated_data):
        """
        Parameters
        ----------
        validated_data : dict

        Returns
        -------
        object
            returns object after inserting data successfully
        """
        feedback_ranges_data = []
        feedback_values_data = validated_data.pop("fv_feedbacks")
        if "fr_feedbacks" in validated_data:
            feedback_ranges_data = validated_data.pop("fr_feedbacks")
        feedback = Feedback.objects.create(**validated_data)
        for feedback_value in feedback_values_data:
            FeedbackValue.objects.create(feedback=feedback, **feedback_value)
        for feedback_range in feedback_ranges_data:
            FeedbackRange.objects.create(feedback=feedback, **feedback_range)
        return feedback

    def update(self, instance, validated_data):
        """
        Parameters
        ----------
        instance : model object
        validated_data : dict

        Returns
        -------
        model object
            returns models object after updating instance name, deleting objects and inseritng new records.
        """
        feedback_ranges_data = []
        feedback_values_data = validated_data.pop("fv_feedbacks")
        if "fr_feedbacks" in validated_data:
            feedback_ranges_data = validated_data.pop("fr_feedbacks")
        instance.name = validated_data["name"]
        instance.save()
        FeedbackRange.objects.filter(feedback=instance.id).delete()
        FeedbackValue.objects.filter(feedback=instance.id).delete()
        for feedback_value in feedback_values_data:
            FeedbackValue.objects.create(feedback=instance, **feedback_value)
        for feedback_range in feedback_ranges_data:
            FeedbackRange.objects.create(feedback=instance, **feedback_range)
        return instance
