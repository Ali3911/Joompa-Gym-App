"""Reps in Reserve models file."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.fitness_level.models import FitnessLevel
from apps.goal.models import Goal


class RepsInReserve(models.Model):
    """RepsInReserve class

    Parameters
    ----------
    models : django.db
    """

    fitness_level = models.ForeignKey(FitnessLevel, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    weeks = models.JSONField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("fitness_level", "goal")


class RepsRange(models.Model):
    """RepsRange class

    RepsRange model with unique constraint on goal, value and range_name field.

    Parameters
    ----------
    models : django.db
    """

    goal = models.ForeignKey(Goal, related_name="goals", on_delete=models.CASCADE)
    value = models.PositiveIntegerField()
    range_name = models.CharField(max_length=2)

    class Meta:
        unique_together = ("goal", "value", "range_name")

    def __str__(self):
        return f"{self.goal}-{self.value}-{self.range_name}"


class RepsRating(models.Model):
    """RepsRating class

    RepsRating model with unique constraint on rating and reps_range field.

    Parameters
    ----------
    models : django.db
    """

    weight = models.IntegerField()
    reps = models.IntegerField()
    rating = models.IntegerField(validators=[MaxValueValidator(3), MinValueValidator(-3)])
    reps_range = models.ForeignKey(RepsRange, related_name="reps_ranges", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("rating", "reps_range")

    def to_dict(self):
        return {
            "id": self.id,
            "weight": self.weight,
            "reps": self.reps,
            "rating": self.rating,
            "reps_range": self.reps_range.id,
        }

    def __str__(self):
        return f"{self.weight}-{self.reps}-{self.rating}-{self.reps_range}"
