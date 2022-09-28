"""Reps in Reserve urls file."""
from django.urls import path

from apps.reps_in_reserve.views import (
    RepsConfigurationsView,
    RepsConfigurationView,
    RepsInReservesView,
    RepsInReserveView,
)

urlpatterns = [
    path("reps-in-reserves/", RepsInReservesView.as_view()),
    path("reps-in-reserves/<int:pk>/", RepsInReserveView.as_view()),
    path("reps-configurations/", RepsConfigurationsView.as_view()),
    path("reps-configuration/<int:goal_id>/", RepsConfigurationView.as_view()),
]
