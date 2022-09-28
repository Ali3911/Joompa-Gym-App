"""Feedback urls file."""
from django.urls import path

from apps.feedback.views import FeedbacksView, FeedbackView

urlpatterns = [
    path("feedbacks/", FeedbacksView.as_view()),
    path("feedback/<int:pk>/", FeedbackView.as_view()),
]
