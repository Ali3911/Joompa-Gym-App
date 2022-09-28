"""Notification serializers file."""
from rest_framework import serializers

from apps.notification.models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer class for model UserNotification


    Parameters
    ----------
    serializers : rest_framework

    """

    class Meta:
        """Meta class for Serializer UserNotificationSerializer"""

        model = UserNotification
        fields = "__all__"
