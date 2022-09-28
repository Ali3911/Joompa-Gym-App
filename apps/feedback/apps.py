"""Feedback config file."""
from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    """FeedbackConfig class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.feedback"
