"""Session config file."""
from django.apps import AppConfig


class SessionConfig(AppConfig):
    """Session configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.session"
