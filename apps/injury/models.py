"""Injury models file."""
from django.db import models

from apps.body_part.models import BodyPart


class InjuryType(models.Model):
    """InjuryType model class

    Parameters
    ----------
    models : django.db

    """

    name = models.CharField(max_length=250)


class Injury(models.Model):
    """Injury model class

    Parameters
    ----------
    models : django.db

    """

    name = models.CharField(max_length=250)
    required = models.BooleanField(default=True)
    injury_type = models.ForeignKey(InjuryType, on_delete=models.CASCADE, related_name="injuries_type")
    body_part = models.ForeignKey(BodyPart, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for model Injury"""

        ordering = ["-created_at"]
        unique_together = ("name", "body_part", "injury_type")
