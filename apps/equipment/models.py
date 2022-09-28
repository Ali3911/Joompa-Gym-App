from django.db import models

from apps.equipment.validators import validate_file_size


class EquipmentOption(models.Model):
    name = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Equipment(models.Model):
    types = (
        ("Adjustable", "Adjustable"),
        ("Preset 1", "Preset 1"),
        ("Preset 2", "Preset 2"),
    )
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(
        max_length=250, null=True, blank=True, upload_to="media/", validators=[validate_file_size]
    )
    level_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    weight = models.JSONField(null=True, blank=True)
    type = models.CharField(max_length=20, default="Preset 1", choices=types)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "level_id": self.level_id,
            "weight": self.weight,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "type": self.type,
        }

    class Meta:
        ordering = ["-created_at"]
