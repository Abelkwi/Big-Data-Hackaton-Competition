import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from google.auth.exceptions import GoogleAuthError
from rest_framework_simplejwt.tokens import RefreshToken

from dashboard.audit import record_event

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


def get_verified_google_email(credential):
    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    if not client_id:
        raise serializers.ValidationError(
            {"google_credential": "Google verification is not configured."}
        )
    if not isinstance(credential, str) or not credential:
        raise serializers.ValidationError(
            {"google_credential": "A Google credential is required."}
        )
    try:
        claims = verify_google_id_token(credential, client_id)
    except (ValueError, GoogleAuthError):
        raise serializers.ValidationError(
            {"google_credential": "The Google credential is invalid or expired."}
        )
    email = claims.get("email")
    if (
        not isinstance(email, str)
        or not email.strip()
        or claims.get("email_verified") is not True
        or not isinstance(claims.get("sub"), str)
        or not claims["sub"]
    ):
        raise serializers.ValidationError(
            {"google_credential": "Google must provide a verified email address."}
        )
    return email.strip().lower()


class GoogleVerifyView(APIView):
    """Verify a Google identity without creating or signing in to an account."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = get_verified_google_email(request.data.get("credential"))
        return Response({"email": email, "email_verified": True})


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
        configured_admin_email = getattr(settings, "ADMIN_LOGIN_EMAIL", "")
        if email == configured_admin_email:
            record_event(
                "login_failed",
                request=request,
                user_identifier=email,
                description="Administrator accounts cannot use Google sign-in",
                metadata={"auth_method": "google"},
            )
            return Response(
                {"detail": "Administrator accounts must use administrator sign-in."},
                status=status.HTTP_403_FORBIDDEN,
            )
        given_name = claims.get("given_name")
        family_name = claims.get("family_name")

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if user is not None and (user.role == "admin" or user.is_staff):
                record_event(
                    "login_failed",
                    request=request,
                    user=user,
                    description="Administrator accounts cannot use Google sign-in",
                    metadata={"auth_method": "google"},
                )
                return Response(
                    {"detail": "Administrator accounts must use administrator sign-in."},
                    status=status.HTTP_403_FORBIDDEN,
                )
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
                record_event(
                    "login_failed",
                    request=request,
                    user=user,
                    description="Inactive account attempted Google sign-in",
                    metadata={"auth_method": "google"},
                )
                return Response(
                    {"detail": "This account is inactive. Contact support for help."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        record_event(
            "login_success",
            request=request,
            user=user,
            description="Signed in with Google",
            metadata={"auth_method": "google"},
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
        email = get_verified_google_email(
            self.request.data.get("google_credential")
        )
        if email != serializer.validated_data["email"].strip().lower():
            raise serializers.ValidationError(
                {"google_credential": "Verify the same email address used for registration."}
            )
        serializer.save(role="farmer", is_verified=True)


class BuyerRegisterView(generics.CreateAPIView):
    """Register a new buyer."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.save(role="buyer")


class NGORegisterView(generics.CreateAPIView):
    """Register a new NGO/Cooperative."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.save(role="ngo")


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