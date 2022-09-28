"""BodyPart urls file."""
from django.urls import path

from apps.body_part.views import BodyPartsView, BodyPartView

urlpatterns = [
    path("body-parts/", BodyPartsView.as_view()),
    path("body-part/<int:pk>/", BodyPartView.as_view()),
]
