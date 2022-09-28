"""Account urls file."""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.urls import path

from apps.accounts.views import LogoutView, UsersAPIView

urlpatterns = [
    path("logout/", LogoutView.as_view(), name="auth_logout"),
    path(r"token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(r"token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", UsersAPIView.as_view()),
]
