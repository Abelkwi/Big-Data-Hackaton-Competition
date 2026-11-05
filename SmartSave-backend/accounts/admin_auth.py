from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError

from dashboard.audit import record_event


User = get_user_model()


class AuditedTokenObtainPairSerializer(TokenObtainPairSerializer):
    allow_admins = False

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        request = self.context.get("request")
        if not self.allow_admins and User.objects.filter(
            email__iexact=identifier
        ).filter(Q(role="admin") | Q(is_staff=True)).exists():
            record_event(
                "login_failed",
                request=request,
                user_identifier=str(identifier),
                description="Administrator accounts must use administrator sign-in",
            )
            raise AuthenticationFailed("Use administrator sign-in.")
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            record_event(
                "login_failed",
                request=request,
                user_identifier=str(identifier),
                description="Failed sign-in attempt",
            )
            raise
        record_event(
            "login_success",
            request=request,
            user=self.user,
            description="Successful sign-in",
        )
        return data


class AuditedTokenObtainPairView(TokenObtainPairView):
    serializer_class = AuditedTokenObtainPairSerializer


class AdminTokenObtainPairSerializer(AuditedTokenObtainPairSerializer):
    allow_admins = True

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        allowed_email = getattr(settings, "ADMIN_LOGIN_EMAIL", "")
        user_is_authorized = User.objects.filter(
            email__iexact=identifier,
            role="admin",
            is_staff=True,
            is_active=True,
            is_verified=True,
        ).exists()
        if (
            not allowed_email
            or identifier.strip().lower() != allowed_email
            or not user_is_authorized
        ):
            record_event(
                "login_failed",
                request=self.context.get("request"),
                user_identifier=str(identifier),
                description="Unauthorized administrator sign-in attempt",
            )
            raise AuthenticationFailed("Invalid administrator credentials.")
        return super().validate(attrs)


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "admin_login"


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not isinstance(refresh_token, str) or not refresh_token:
            return Response(
                {"detail": "A refresh token is required to sign out."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "The refresh token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record_event(
            "logout",
            request=request,
            user=request.user,
            description="Signed out",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
