"""BaselineAssessment config file."""
from django.apps import AppConfig


class BaselineAssessmentConfig(AppConfig):
    """BaselineAssessment configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.baseline_assessment"
