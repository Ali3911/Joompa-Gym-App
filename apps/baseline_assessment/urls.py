"""BaselineAssessment urls file."""
from django.urls import path

from apps.baseline_assessment.views import BaselineAssessmentsView, BaselineAssessmentView

urlpatterns = [
    path("baseline/assessments/", BaselineAssessmentsView.as_view()),
    path("baseline/assessment/<int:pk>/", BaselineAssessmentView.as_view()),
]
