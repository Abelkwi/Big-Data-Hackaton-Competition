from django.contrib.auth import get_user_model

from .models import AuditEvent
from notifications.models import Notification


User = get_user_model()

ADMIN_NOTIFICATION_EVENTS = {
    "registration": ("New user registration", "users"),
    "content_submit": ("New content submission", "content"),
    "post_create": ("New platform post", "content"),
    "login_failed": ("Failed login attempt", "activity"),
    "security_event": ("Security alert", "activity"),
}


def record_event(
    event_type,
    *,
    request=None,
    user=None,
    user_identifier="",
    description="",
    metadata=None,
    actor=None,
):
    if user is not None:
        user_identifier = user.email
    event = AuditEvent.objects.create(
        event_type=event_type,
        user=user,
        actor=actor,
        user_identifier=(user_identifier or "")[:254],
        user_role=user.role if user is not None else "",
        description=description[:255],
        metadata=metadata or {},
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
    )
    notification = ADMIN_NOTIFICATION_EVENTS.get(event_type)
    if notification:
        title, section = notification
        identifier = event.user_identifier or "Unknown account"
        detail = event.description or event.get_event_type_display()
        Notification.objects.bulk_create(
            [
                Notification(
                    recipient=admin,
                    notification_type="security" if event_type in {"login_failed", "security_event"} else "system",
                    title=title,
                    body=f"{identifier}: {detail}"[:1000],
                    link=f"/admin-dashboard.html#{section}",
                )
                for admin in User.objects.filter(is_staff=True, is_active=True)
            ]
        )
    return event
