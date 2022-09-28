"""Session urls file."""
from django.urls import path

from apps.session.views import SessionsView, SessionView

urlpatterns = [
    path("sessions/", SessionsView.as_view()),
    path("session/<int:pk>/", SessionView.as_view()),
]
