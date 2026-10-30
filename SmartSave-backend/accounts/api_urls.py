"""Authentication API endpoints."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views

urlpatterns = [
    # JWT Auth
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    
    # Registration
    path("register/", api_views.RegisterView.as_view(), name="auth-register"),
    path("register/farmer/", api_views.FarmerRegisterView.as_view(), name="auth-register-farmer"),
    path("register/buyer/", api_views.BuyerRegisterView.as_view(), name="auth-register-buyer"),
    path("register/ngo/", api_views.NGORegisterView.as_view(), name="auth-register-ngo"),
    
    # Profile
    path("profile/", api_views.ProfileView.as_view(), name="auth-profile"),
    path("profile/update/", api_views.ProfileUpdateView.as_view(), name="auth-profile-update"),
    path("profile/change-password/", api_views.ChangePasswordView.as_view(), name="auth-change-password"),
]