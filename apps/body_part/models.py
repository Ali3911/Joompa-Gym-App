"""BodyPart models file."""
from django.db import models


class BodyPart(models.Model):
    """BodyPart model class

    Parameters
    ----------
    models : django.db

    """

    name = models.CharField(max_length=100)
    classification = models.ForeignKey(
        "self", related_name="classifications", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    required = models.BooleanField(default=True)

    class Meta:
        """Meta class for model BodyPart"""

        ordering = ["-created_at"]
        verbose_name = "Body Part"
        verbose_name_plural = "Body Parts"
