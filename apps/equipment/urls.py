from django.urls import path

from apps.equipment.views import EquipmentOptionsView, EquipmentsView, EquipmentView

urlpatterns = [
    path("equipments/", EquipmentsView.as_view()),
    path("equipment/<int:pk>/", EquipmentView.as_view()),
    path("equipment-options/", EquipmentOptionsView.as_view(), name="equipment_options"),
]
