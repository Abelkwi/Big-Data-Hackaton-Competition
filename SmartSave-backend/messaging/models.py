from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    """A conversation thread between two or more users."""

    participants = models.ManyToManyField(
        User, related_name="conversations"
    )
    subject = models.CharField(max_length=200, blank=True)
    product = models.ForeignKey(
        "marketplace.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()

    @property
    def participant_names(self):
        return [u.get_full_name() or u.email for u in self.participants.all()]

    def __str__(self):
        return self.subject or f"Conversation #{self.id}"


class Message(models.Model):
    """Individual message within a conversation."""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sender_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.email}: {self.body[:50]}..."