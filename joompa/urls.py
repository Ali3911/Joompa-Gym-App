"""joompa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

import joompa.settings as settings

from django.conf.urls.static import static
from django.urls import include, path

schema_view = get_schema_view(
    openapi.Info(
        title="Joompa API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    url=settings.db_config["BASE_URL"],
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("api/", include("apps.equipment.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.reps_in_reserve.urls")),
    path("api/", include("apps.baseline_assessment.urls")),
    path("api/", include("apps.injury.urls")),
    path("api/", include("apps.goal.urls")),
    path("api/", include("apps.session.urls")),
    path("api/", include("apps.fitness_level.urls")),
    path("api/", include("apps.standard_variable.urls")),
    path("api/", include("apps.variance.urls")),
    path("api/", include("apps.body_part.urls")),
    path("api/", include("apps.controlled.urls")),
    path("api/", include("apps.feedback.urls")),
    path("api/", include("apps.mobile_api.v1.urls")),
    path("api/", include("apps.config.urls")),
    path("api/", include("apps.notification.urls")),
    path("api-docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
