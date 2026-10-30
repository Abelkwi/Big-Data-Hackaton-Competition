from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    """System notification for a user."""

    TYPE_CHOICES = [
        ("order", "Order Update"),
        ("message", "New Message"),
        ("marketplace", "Marketplace"),
        ("verification", "Verification"),
        ("recovery", "Food Recovery"),
        ("blog", "Blog"),
        ("system", "System"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default="system"
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"