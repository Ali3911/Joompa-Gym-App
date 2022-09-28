"""Injury config file."""
from django.apps import AppConfig


class InjuryConfig(AppConfig):
    """Injury configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.injury"
