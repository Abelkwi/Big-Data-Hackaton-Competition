from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "sender", "sender_name",
            "sender_email", "body", "is_read", "created_at",
        ]
        read_only_fields = ["id", "sender", "is_read", "created_at"]

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email

    def get_sender_email(self, obj):
        return obj.sender.email


class SendMessageSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1)

    def validate_body(self, value):
        return value.strip()


class ConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "subject", "product", "product_name",
            "participant_names", "last_message",
            "unread_count", "created_at", "updated_at",
        ]

    def get_last_message(self, obj):
        msg = obj.last_message
        if msg:
            return {
                "sender": msg.sender.email,
                "body": msg.body[:100],
                "created_at": msg.created_at,
            }
        return None

    def get_participant_names(self, obj):
        return obj.participant_names

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participant_names = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "subject", "product", "product_name",
            "participant_names", "messages",
            "created_at", "updated_at",
        ]

    def get_participant_names(self, obj):
        return obj.participant_names

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None


class CreateConversationSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    subject = serializers.CharField(required=False, allow_blank=True, max_length=200)
    body = serializers.CharField(min_length=1)
    product_id = serializers.IntegerField(required=False, allow_null=True)