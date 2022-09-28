"""StandardVariable models file."""
from django.db import models


# Create your models here.
class StandardVariable(models.Model):
    """StandardVariable model class

    Parameters
    ----------
    models : django.db

    """

    name = models.CharField(max_length=250, unique=True)
    ui_control_type = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=True)
    is_personalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_type = models.CharField(max_length=250)

    class Meta:
        """Meta class for model StandardVariable"""

        ordering = ["-created_at"]
