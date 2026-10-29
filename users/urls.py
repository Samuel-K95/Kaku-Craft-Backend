from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ChangePasswordView, CustomTokenObtainPairView, MeView, ProfileUpdateView, RegisterView

app_name = "users"

urlpatterns = [
    path("auth/signup/", RegisterView.as_view(), name="signup"),
    path("auth/signin/", CustomTokenObtainPairView.as_view(), name="signin"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", MeView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="edit-profile"),
    path("profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
]
