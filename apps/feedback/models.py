"""Feedback models file."""
from django.db import models


# Create your models here.
class Feedback(models.Model):
    """Feedback class

    Parameters
    ----------
    models : django.db
    """

    types = (
        ("pre_session", "pre_session"),
        ("post_session", "post_session"),
    )
    name = models.CharField(max_length=250)
    type = models.CharField(max_length=20, default="pre_session", choices=types)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("name", "type")


class FeedbackValue(models.Model):
    """FeedbackValue class

    Parameters
    ----------
    models : django.db
    """

    description = models.CharField(max_length=250)
    value = models.PositiveIntegerField()
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="fv_feedbacks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackRange(models.Model):
    """FeedbackRange class

    Parameters
    ----------
    models : django.db
    """

    name = models.CharField(max_length=250)
    rir = models.CharField(max_length=250)
    range_lower_limit = models.PositiveIntegerField()
    range_upper_limit = models.PositiveIntegerField()
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="fr_feedbacks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
