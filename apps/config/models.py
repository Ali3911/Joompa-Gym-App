from django.db import models


class Config(models.Model):
    key = models.CharField(max_length=250)
    value = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
