"""Session models file."""
from django.core.validators import MaxValueValidator
from django.db import models


class Session(models.Model):
    """Session model class

    Parameters
    ----------
    models : django.db

    """

    description = models.CharField(max_length=100)
    value = models.PositiveIntegerField(validators=[MaxValueValidator(6)], unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for model Session"""

        ordering = ["-created_at"]
