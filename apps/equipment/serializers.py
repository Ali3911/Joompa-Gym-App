from rest_framework import serializers

from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.equipment.models import Equipment, EquipmentOption


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"

    def create(self, validated_data):
        if "image" not in validated_data.keys():
            validated_data["image"] = "media/default.png"
        elif not isinstance(validated_data["image"], InMemoryUploadedFile):
            validated_data["image"] = "media/default.png"
        return Equipment.objects.create(**validated_data)


class CustomeEquipmentSerializer(serializers.ModelSerializer):
    types = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)

    class Meta:
        model = Equipment
        fields = ["name", "image", "weight", "types", "type"]
        read_only_fields = ["level_id"]


class EquipmentOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentOption
        fields = "__all__"
