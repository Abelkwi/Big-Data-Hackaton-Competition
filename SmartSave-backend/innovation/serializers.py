from rest_framework import serializers
from .models import InnovationIdea, InnovationVote, InnovationComment


class InnovationCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = InnovationComment
        fields = ["id", "idea", "author", "author_name", "body", "created_at"]
        read_only_fields = ["id", "author", "author_name", "created_at"]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.email


class InnovationIdeaListSerializer(serializers.ModelSerializer):
    submitter_name = serializers.SerializerMethodField()
    votes_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = InnovationIdea
        fields = [
            "id", "title", "slug", "description", "category", "status",
            "submitter_name", "votes_count", "comment_count",
            "is_featured", "created_at",
        ]

    def get_submitter_name(self, obj):
        return obj.submitted_by.get_full_name() or obj.submitted_by.email

    def get_comment_count(self, obj):
        return obj.comments.count()


class InnovationIdeaDetailSerializer(serializers.ModelSerializer):
    submitter_name = serializers.SerializerMethodField()

    class Meta:
        model = InnovationIdea
        fields = [
            "id", "title", "slug", "description", "problem_solved",
            "expected_impact", "category", "status", "attachments",
            "submitted_by", "submitter_name", "votes_count",
            "is_featured", "created_at", "updated_at",
        ]

    def get_submitter_name(self, obj):
        return obj.submitted_by.get_full_name() or obj.submitted_by.email