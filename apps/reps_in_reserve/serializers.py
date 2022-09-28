"""Reps in Reserve serializers file."""
from rest_framework import serializers

from apps.fitness_level.serializers import FitnessLevelSerializer
from apps.goal.serializers import GoalSerializer
from apps.reps_in_reserve.models import RepsInReserve, RepsRange, RepsRating


class RepsInReserveSerializer(serializers.ModelSerializer):
    """RepsInReserveSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    class Meta:
        model = RepsInReserve
        fields = "__all__"

    def to_representation(self, instance):
        """to_representation function

        Returns JSON object in structured form.

        Parameters
        ----------
        instance : model object

        Returns
        -------
        JSON object
        """
        response = super().to_representation(instance)
        response["goals"] = GoalSerializer(instance.goal).data
        response["fitness_levels"] = FitnessLevelSerializer(instance.fitness_level).data
        del response["fitness_level"], response["goal"]
        return response


class CustomeRepsInReserveSerializer(serializers.ModelSerializer):
    weeks = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)

    class Meta:
        model = RepsInReserve
        fields = ["weeks", "fitness_level", "goal"]
        # read_only_fields = ['level_id']

    def to_representation(self, instance):
        """to_representation function

        Returns JSON object in structured form.

        Parameters
        ----------
        instance : model object

        Returns
        -------
        JSON object
        """
        response = super().to_representation(instance)
        response["goals"] = GoalSerializer(instance.goal).data
        response["fitness_levels"] = FitnessLevelSerializer(instance.fitness_level).data
        del response["fitness_level"], response["goal"]
        return response


class RepsRatingSerializer(serializers.ModelSerializer):
    """RepsRatingSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    class Meta:
        model = RepsRating
        fields = ["id", "weight", "reps", "rating"]


class RepsRangeSerializer(serializers.ModelSerializer):
    """RepsRangeSerializer class

    Parameters
    ----------
    serializers : rest_framework
    """

    reps_ranges = RepsRatingSerializer(many=True)

    class Meta:
        model = RepsRange
        fields = ["id", "goal", "value", "range_name", "reps_ranges"]

    def to_representation(self, instance):
        """to_representation function

        Returns JSON object in structured form.

        Parameters
        ----------
        instance : model object

        Returns
        -------
        JSON object
        """
        response = super().to_representation(instance)
        response["goal"] = GoalSerializer(instance.goal).data
        del response["goal"]["required"]
        del response["goal"]["created_at"]
        del response["goal"]["updated_at"]
        return response

    def create(self, validated_data):
        """create function

        Create function saves data in RepsRange table and RepsRating table along with reps_range id.

        Parameters
        ----------
        validated_data : dict

        Returns
        -------
        model object
        """
        reps_ratings = validated_data.pop("reps_ranges")
        reps_range = RepsRange.objects.create(**validated_data)
        for reps_rating in reps_ratings:
            RepsRating.objects.create(reps_range=reps_range, **reps_rating)
        return reps_range

    def update(self, instance, validated_data):
        """update function

        Update function updates data in RepsRating table.

        Parameters
        ----------
        instance : model object
        validated_data : dict

        Returns
        -------
        model object
        """

        instance.value = validated_data.get("value", instance.value)
        instance.save()
        reps_ratings = list(instance.reps_ranges.all())
        for data in validated_data["reps_ranges"]:
            rating_data = reps_ratings.pop(0)
            RepsRating.objects.filter(pk=rating_data.pk).update(**data)
        return instance
