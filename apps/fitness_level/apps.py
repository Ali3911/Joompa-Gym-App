"""FitnessLevel config file."""
from django.apps import AppConfig


class FitnessLevelConfig(AppConfig):
    """FitnessLevel configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fitness_level"
