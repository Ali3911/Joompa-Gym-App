from django.db import models

from apps.mobile_api.v1.models import UserProfile


class UserNotification(models.Model):
    user_profile_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_notification")
    registration_id = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
