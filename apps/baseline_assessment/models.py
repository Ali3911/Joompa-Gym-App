"""BaselineAssessment models file."""
from django.db import models


class BaselineAssessment(models.Model):
    """BaselineAssessment model class

    Parameters
    ----------
    models : django.db

    """

    question = models.CharField(max_length=250, unique=True)
    control_type = models.CharField(max_length=100)
    required = models.BooleanField(default=True)
    options = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for model BaselineAssessment"""

        ordering = ["-created_at"]
