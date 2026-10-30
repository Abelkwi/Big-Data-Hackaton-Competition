from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "is_read", "created_at")
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "product", "participant_list", "message_count", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("subject", "participants__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MessageInline]

    def participant_list(self, obj):
        return ", ".join(obj.participant_names)
    participant_list.short_description = "Participants"

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "body_preview", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("body", "sender__email")
    readonly_fields = ("created_at",)

    def body_preview(self, obj):
        return obj.body[:80] + "..." if len(obj.body) > 80 else obj.body
    body_preview.short_description = "Message"