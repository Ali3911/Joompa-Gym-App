from rest_framework import serializers

from apps.accounts.models import User
from apps.mobile_api.v1.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id"]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["email"] = instance.user_id.email
        response["first_name"] = instance.user_id.first_name
        response["last_name"] = instance.user_id.last_name
        response["phone_number"] = instance.user_id.phone_number
        response["created_at"] = instance.created_at
        return response
