from django.urls import path

from apps.mobile_api.v1.views import UserFeedbackView, UserProfileView, UserProgramDesignView, UserWorkoutProgramsView

urlpatterns = [
    path("user-workout-programs/", UserWorkoutProgramsView.as_view()),
    path("user-profile/", UserProfileView.as_view()),
    path("user-feedback/", UserFeedbackView.as_view()),
    path("user-programs-designs/<int:user_id>/", UserProgramDesignView.as_view()),
]
