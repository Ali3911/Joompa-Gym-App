from rest_framework import serializers

from apps.variance.models import Variance


class VarianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variance
        fields = "__all__"
