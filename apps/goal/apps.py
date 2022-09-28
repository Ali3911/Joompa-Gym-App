"""Goal config file."""
from django.apps import AppConfig


class GoalConfig(AppConfig):
    """Goal configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.goal"
