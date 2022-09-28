"""Accounts config file."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Accounts configuration class.

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
