"""Config urls file."""
from django.urls import path

from apps.config.views import ConfigsView, ConfigView

urlpatterns = [
    path("configs/", ConfigsView.as_view()),
    path("config/<int:pk>/", ConfigView.as_view()),
]
