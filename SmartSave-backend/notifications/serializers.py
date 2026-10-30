from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_label = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id", "recipient", "notification_type", "type_label",
            "title", "body", "link", "is_read", "created_at",
        ]
        read_only_fields = ["id", "recipient", "created_at"]

    def get_type_label(self, obj):
        return obj.get_notification_type_display()