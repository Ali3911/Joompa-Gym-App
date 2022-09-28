"""StandardVariable urls file."""
from django.urls import path

from apps.standard_variable.views import StandardVariablesView, StandardVariableView

urlpatterns = [
    path("standard-variables/", StandardVariablesView.as_view()),
    path("standard-variable/<int:pk>/", StandardVariableView.as_view()),
]
