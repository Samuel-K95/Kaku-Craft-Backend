from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminUserDetailView,
    AdminUserListView,
    ChangePasswordView,
    CustomTokenObtainPairView,
    ImpersonateView,
    MeView,
    ProfileUpdateView,
    RegisterView,
)

app_name = "users"

urlpatterns = [
    path("auth/signup/", RegisterView.as_view(), name="signup"),
    path("auth/signin/", CustomTokenObtainPairView.as_view(), name="signin"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/impersonate/", ImpersonateView.as_view(), name="impersonate"),
    path("profile/", MeView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="edit-profile"),
    path("profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("manage/", AdminUserListView.as_view(), name="manage-list"),
    path("manage/<int:pk>/", AdminUserDetailView.as_view(), name="manage-detail"),
]
