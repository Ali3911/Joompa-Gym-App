"""Injury urls file."""
from django.urls import path

from apps.injury.views import InjuriesView, InjuryTypesView, InjuryView

urlpatterns = [
    path("injuries/", InjuriesView.as_view()),
    path("injury/<int:pk>/", InjuryView.as_view()),
    path("injury-types/", InjuryTypesView.as_view()),
]
