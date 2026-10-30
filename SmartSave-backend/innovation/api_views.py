from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import InnovationIdea, InnovationVote, InnovationComment
from .serializers import (
    InnovationIdeaListSerializer,
    InnovationIdeaDetailSerializer,
    InnovationCommentSerializer,
)


class InnovationIdeaListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InnovationIdeaListSerializer

    def get_queryset(self):
        qs = InnovationIdea.objects.exclude(status="draft").select_related(
            "submitted_by"
        )
        search = self.request.query_params.get("search", "")
        category = self.request.query_params.get("category", "")
        if search:
            qs = qs.filter(title__icontains=search)
        if category:
            qs = qs.filter(category=category)
        return qs


class InnovationIdeaDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            idea = (
                InnovationIdea.objects.select_related("submitted_by")
                .prefetch_related("comments__author")
                .get(slug=slug)
            )
        except InnovationIdea.DoesNotExist:
            return Response({"detail": "Idea not found."}, status=404)

        data = InnovationIdeaDetailSerializer(idea).data
        data["comments"] = InnovationCommentSerializer(
            idea.comments.all(), many=True
        ).data
        has_voted = False
        if request.user.is_authenticated:
            has_voted = idea.votes.filter(voter=request.user).exists()
        data["has_voted"] = has_voted
        return Response(data)


class InnovationIdeaCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InnovationIdeaDetailSerializer

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class ToggleVoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            idea = InnovationIdea.objects.get(slug=slug)
        except InnovationIdea.DoesNotExist:
            return Response({"detail": "Idea not found."}, status=404)

        vote, created = InnovationVote.objects.get_or_create(
            idea=idea, voter=request.user
        )
        if not created:
            vote.delete()
            idea.votes_count = max(0, idea.votes_count - 1)
            idea.save(update_fields=["votes_count"])
            return Response(
                {"detail": "Vote removed.", "votes_count": idea.votes_count}
            )
        idea.votes_count += 1
        idea.save(update_fields=["votes_count"])
        return Response(
            {"detail": "Vote added.", "votes_count": idea.votes_count},
            status=201,
        )


class AddCommentView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InnovationCommentSerializer

    def perform_create(self, serializer):
        idea = InnovationIdea.objects.get(slug=self.kwargs["slug"])
        serializer.save(idea=idea, author=self.request.user)


class FeaturedIdeasView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InnovationIdeaListSerializer

    def get_queryset(self):
        return (
            InnovationIdea.objects.filter(is_featured=True)
            .exclude(status="draft")
            .select_related("submitted_by")[:6]
        )