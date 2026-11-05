from django.conf import settings
from rest_framework.permissions import BasePermission


class IsConfiguredAdmin(BasePermission):
    message = "Administrator access is not available for this account."

    def has_permission(self, request, view):
        user = request.user
        allowed_email = getattr(settings, "ADMIN_LOGIN_EMAIL", "")
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_verified
            and user.is_staff
            and user.role == "admin"
            and allowed_email
            and user.email.lower() == allowed_email
        )
