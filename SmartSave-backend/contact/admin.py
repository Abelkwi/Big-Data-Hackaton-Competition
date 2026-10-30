from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "replied", "created_at")
    list_filter = ("is_read", "replied", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    list_editable = ("is_read", "replied")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {
            "fields": ("name", "email", "subject"),
        }),
        ("Message", {
            "fields": ("message",),
        }),
        ("Status", {
            "fields": ("is_read", "replied", "created_at"),
        }),
    )
