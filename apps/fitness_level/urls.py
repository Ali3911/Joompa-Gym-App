"""FitnessLevel urls file."""
from django.urls import path

from apps.fitness_level.views import FitnessLevelsView, FitnessLevelView

urlpatterns = [
    path("fitness/levels/", FitnessLevelsView.as_view()),
    path("fitness/level/<int:pk>/", FitnessLevelView.as_view()),
]
