from django.urls import path

from apps.controlled.views import (
    ControlProgramsView,
    ControlProgramView,
    EquipmentCombinationView,
    EquipmentRelationsView,
    EquipmentRelationView,
    ExerciseRelationshipsView,
    ExerciseRelationshipView,
    ExercisesView,
    FirstEverCalcsView,
    FirstEverCalcView,
    ProgramDesignsView,
    ProgramDesignView,
    SessionLengthsView,
    SessionLengthView,
    VideosView,
    VideoView,
)

urlpatterns = [
    path("session-lengths/", SessionLengthView.as_view(), name="session-lengths"),
    path("session-length/<int:pk>/", SessionLengthsView.as_view(), name="session-length"),
    path("program-designs/", ProgramDesignsView.as_view(), name="program-designs"),
    path("program-design/<int:session_length_id>/", ProgramDesignView.as_view(), name="program-design"),
    path("first-ever-calcs/", FirstEverCalcsView.as_view()),
    path("first-ever-calc/<int:pk>/", FirstEverCalcView.as_view()),
    path("control-programs/", ControlProgramsView().as_view()),
    path("control-program/<int:pk>/", ControlProgramView().as_view()),
    path("exercises/", ExercisesView.as_view()),
    path("exercise-relationships/", ExerciseRelationshipsView.as_view()),
    path("exercise-relationship/<int:id>/", ExerciseRelationshipView.as_view()),
    path("equipment-relations/", EquipmentRelationsView.as_view()),
    path("equipment-relation/<int:cp_id>/", EquipmentRelationView.as_view()),
    path("equipment-combination/<int:pk>/", EquipmentCombinationView.as_view()),
    path("videos/", VideosView.as_view()),
    path("video/<int:id>/", VideoView.as_view()),
]
