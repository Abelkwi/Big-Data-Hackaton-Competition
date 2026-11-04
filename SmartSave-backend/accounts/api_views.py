import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from google.auth.exceptions import GoogleAuthError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, FarmerProfile, BuyerProfile, NGOProfile
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    FarmerProfileSerializer,
    BuyerProfileSerializer,
    NGOProfileSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


def verify_google_id_token(token, client_id):
    from google.auth.transport.requests import Request
    from google.oauth2.id_token import verify_oauth2_token

    return verify_oauth2_token(token, Request(), audience=client_id)


class GoogleLoginView(APIView):
    """Verify a Google ID token and issue SMARTSAVE JWTs."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if not client_id:
            return Response(
                {"detail": "Google sign-in is not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        credential = request.data.get("credential")
        if not isinstance(credential, str) or not credential:
            return Response(
                {"detail": "A Google credential is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            claims = verify_google_id_token(credential, client_id)
        except (ValueError, GoogleAuthError):
            return Response(
                {"detail": "The Google credential is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = claims.get("email")
        if (
            not isinstance(email, str)
            or not email.strip()
            or len(email) > 254
            or claims.get("email_verified") is not True
            or not isinstance(claims.get("sub"), str)
            or not claims["sub"]
        ):
            return Response(
                {"detail": "Google must provide a verified email address."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        email = email.strip().lower()
        given_name = claims.get("given_name")
        family_name = claims.get("family_name")

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                base_username = re.sub(r"[^0-9A-Za-z_.-]+", "", email.split("@", 1)[0])[:140] or "google-user"
                username = base_username
                suffix = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username[:140 - len(str(suffix))]}{suffix}"
                    suffix += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=given_name[:150] if isinstance(given_name, str) else "",
                    last_name=family_name[:150] if isinstance(family_name, str) else "",
                    role="buyer",
                    is_verified=True,
                )
                Profile.objects.get_or_create(user=user)
                BuyerProfile.objects.get_or_create(profile=user.profile)
            elif not user.is_active:
                return Response(
                    {"detail": "This account is inactive. Contact support for help."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })


class RegisterView(generics.CreateAPIView):
    """Register a new user with any role."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class FarmerRegisterView(generics.CreateAPIView):
    """Register a new farmer."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="farmer")
        Profile.objects.get_or_create(user=user)
        FarmerProfile.objects.get_or_create(profile=user.profile)


class BuyerRegisterView(generics.CreateAPIView):
    """Register a new buyer."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="buyer")
        Profile.objects.get_or_create(user=user)
        BuyerProfile.objects.get_or_create(profile=user.profile)


class NGORegisterView(generics.CreateAPIView):
    """Register a new NGO/Cooperative."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(role="ngo")
        Profile.objects.get_or_create(user=user)
        NGOProfile.objects.get_or_create(profile=user.profile)


class ProfileView(APIView):
    """Get current user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        # Add role-specific profile data
        if hasattr(user, "profile"):
            data["profile"] = ProfileSerializer(user.profile).data

        if user.role == "farmer" and hasattr(user.profile, "farmer_profile"):
            data["farmer_profile"] = FarmerProfileSerializer(user.profile.farmer_profile).data

        if user.role == "buyer" and hasattr(user.profile, "buyer_profile"):
            data["buyer_profile"] = BuyerProfileSerializer(user.profile.buyer_profile).data

        if user.role == "ngo" and hasattr(user.profile, "ngo_profile"):
            data["ngo_profile"] = NGOProfileSerializer(user.profile.ngo_profile).data

        return Response(data)


class ProfileUpdateView(generics.UpdateAPIView):
    """Update current user's profile."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class ChangePasswordView(APIView):
    """Change current user's password."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data["new_password"])
            request.user.save()
            return Response({"detail": "Password updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)