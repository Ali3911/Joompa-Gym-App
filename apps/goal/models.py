"""Goal models file."""
from django.db import models


class Goal(models.Model):
    """Goal model class

    Parameters
    ----------
    models : django.db

    """

    type_choice = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Both", "Both"),
    )
    name = models.CharField(max_length=250, unique=True)
    required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    gender = models.CharField(max_length=20, default="Both", choices=type_choice)

    class Meta:
        """Meta class for model Goal"""

        ordering = ["-created_at"]
