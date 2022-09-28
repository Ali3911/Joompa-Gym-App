"""FitnessLevel models file."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class FitnessLevel(models.Model):
    """FitnessLevel model class

    Parameters
    ----------
    models : django.db

    """

    fitness_name = models.CharField(max_length=250, unique=True)
    fitness_number = models.PositiveBigIntegerField(unique=True, validators=[MinValueValidator(1)])
    fitness_level = models.DecimalField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], max_digits=6, decimal_places=3
    )
    required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for model FitnessLevel"""

        ordering = ["-created_at"]
