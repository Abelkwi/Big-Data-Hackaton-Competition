from django.contrib import admin
from .models import BlogCategory, BlogPost, BlogComment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = "Posts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "is_published", "published_at", "created_at")
    list_filter = ("is_published", "category", "created_at")
    search_fields = ("title", "content", "author__email")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    actions = ["publish_posts", "unpublish_posts"]

    def publish_posts(self, request, qs):
        qs.update(is_published=True)
    publish_posts.short_description = "Publish selected"

    def unpublish_posts(self, request, qs):
        qs.update(is_published=False)
    unpublish_posts.short_description = "Unpublish selected"


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "body_preview", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("body", "author__email", "post__title")

    def body_preview(self, obj):
        return obj.body[:80] + "..." if len(obj.body) > 80 else obj.body
    body_preview.short_description = "Comment"