"""Goal urls file."""
from django.urls import path

from apps.goal.views import GoalsView, GoalView

urlpatterns = [
    path("goals/", GoalsView.as_view()),
    path("goal/<int:pk>/", GoalView.as_view()),
]
