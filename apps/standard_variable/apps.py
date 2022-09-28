"""StandardVariable config file."""
from django.apps import AppConfig


class VariableModuleConfig(AppConfig):
    """StandardVariable configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.standard_variable"
