from django.urls import path

from apps.variance.views import VariancesView, VarianceView

urlpatterns = [
    path("variances/", VariancesView.as_view(), name="variances"),
    path("variance/<int:pk>/", VarianceView.as_view(), name="variance"),
]
