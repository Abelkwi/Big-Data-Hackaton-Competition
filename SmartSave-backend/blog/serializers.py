from rest_framework import serializers
from .models import BlogCategory, BlogPost, BlogComment


class BlogCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogCategory
        fields = ["id", "name", "slug", "description", "post_count"]

    def get_post_count(self, obj):
        return obj.posts.filter(is_published=True).count()


class BlogPostListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "slug", "excerpt", "featured_image",
            "author_name", "category_name", "tags", "comment_count",
            "published_at", "created_at",
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.email

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_comment_count(self, obj):
        return obj.comments.filter(is_approved=True).count()


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "slug", "content", "excerpt", "featured_image",
            "author", "author_name", "category", "category_name", "tags",
            "is_published", "published_at", "created_at", "updated_at",
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.email

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class BlogCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = ["id", "post", "author", "author_name", "body", "created_at"]
        read_only_fields = ["id", "author", "author_name", "created_at"]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.email