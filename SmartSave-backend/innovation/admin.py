from django.contrib import admin
from .models import InnovationIdea, InnovationVote, InnovationComment


class InnovationCommentInline(admin.TabularInline):
    model = InnovationComment
    extra = 0
    readonly_fields = ("author", "body", "created_at")


@admin.register(InnovationIdea)
class InnovationIdeaAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "submitted_by",
        "category",
        "status",
        "votes_count",
        "is_featured",
        "created_at",
    )
    list_filter = ("status", "category", "is_featured")
    search_fields = ("title", "description", "submitted_by__email")
    readonly_fields = ("votes_count", "created_at", "updated_at")
    inlines = [InnovationCommentInline]
    actions = ["approve_ideas", "mark_implemented"]

    def approve_ideas(self, request, qs):
        qs.update(status="approved")

    approve_ideas.short_description = "Approve selected"

    def mark_implemented(self, request, qs):
        qs.update(status="implemented")

    mark_implemented.short_description = "Mark as implemented"


@admin.register(InnovationVote)
class InnovationVoteAdmin(admin.ModelAdmin):
    list_display = ("idea", "voter", "created_at")
    search_fields = ("idea__title", "voter__email")


@admin.register(InnovationComment)
class InnovationCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "idea", "author", "body_preview", "created_at")
    search_fields = ("body", "author__email", "idea__title")

    def body_preview(self, obj):
        return obj.body[:80] + "..."