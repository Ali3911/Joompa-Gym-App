"""BodyPart config file."""
from django.apps import AppConfig


class BodyPartsConfig(AppConfig):
    """BodyPart configuration class

    Parameters
    ----------
    AppConfig : django.apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.body_part"
