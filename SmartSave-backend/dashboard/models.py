from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    EVENT_TYPES = [
        ("registration", "Registration"),
        ("login_success", "Successful login"),
        ("login_failed", "Failed login"),
        ("logout", "Logout"),
        ("profile_update", "Profile update"),
        ("post_create", "Post creation"),
        ("content_submit", "Content submission"),
        ("password_reset", "Password reset"),
        ("security_event", "Security event"),
        ("account_suspension", "Account status change"),
        ("admin_action", "Administrative action"),
    ]

    event_type = models.CharField(max_length=32, choices=EVENT_TYPES, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_audit_actions",
    )
    user_identifier = models.EmailField(blank=True, db_index=True)
    user_role = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"


class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ("general", "General announcement"),
        ("important", "Important notice"),
        ("targeted", "Targeted notification"),
    ]
    AUDIENCE_CHOICES = [
        ("all", "Everyone"),
        ("farmer", "Farmers"),
        ("buyer", "Buyers"),
        ("ngo", "NGOs and cooperatives"),
        ("cooperative", "Cooperatives"),
        ("institution", "Institutional partners"),
    ]
    VISIBILITY_CHOICES = [
        ("homepage", "Public homepage"),
        ("dashboard", "User dashboards"),
        ("both", "Homepage and dashboards"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=180)
    body = models.TextField(max_length=5000)
    category = models.CharField(
        max_length=16, choices=CATEGORY_CHOICES, default="general"
    )
    audience = models.CharField(
        max_length=16, choices=AUDIENCE_CHOICES, default="all"
    )
    visibility = models.CharField(
        max_length=16, choices=VISIBILITY_CHOICES, default="both"
    )
    is_pinned = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    notifications_sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_announcements",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_announcements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "publish_at"])]

    def __str__(self):
        return self.title


class ModerationReport(models.Model):
    TARGET_CHOICES = [
        ("user", "User"),
        ("product", "Product"),
        ("post", "Blog post"),
        ("recovery", "Recovery listing"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_reports",
    )
    target_type = models.CharField(max_length=16, choices=TARGET_CHOICES)
    target_id = models.PositiveBigIntegerField()
    reason = models.TextField(max_length=2000)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    resolution = models.CharField(max_length=500, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_moderation_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"Report #{self.pk} on {self.target_type} {self.target_id}"
