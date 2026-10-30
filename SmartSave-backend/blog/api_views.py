from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BlogCategory, BlogPost, BlogComment
from .serializers import (
    BlogCategorySerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogCommentSerializer,
)


class BlogPostListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlogPostListSerializer

    def get_queryset(self):
        qs = BlogPost.objects.filter(is_published=True).select_related(
            "author", "category"
        )
        search = self.request.query_params.get("search", "")
        category = self.request.query_params.get("category", "")
        if search:
            qs = qs.filter(title__icontains=search)
        if category:
            qs = qs.filter(category__slug=category)
        return qs


class BlogPostDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            post = (
                BlogPost.objects.select_related("author", "category")
                .prefetch_related("comments__author")
                .get(slug=slug, is_published=True)
            )
        except BlogPost.DoesNotExist:
            return Response({"detail": "Post not found."}, status=404)

        data = BlogPostDetailSerializer(post).data
        comments = post.comments.filter(is_approved=True)
        data["comments"] = BlogCommentSerializer(comments, many=True).data
        return Response(data)


class BlogPostCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = BlogPostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class BlogPostUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"
    queryset = BlogPost.objects.all()


class BlogPostDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, slug):
        try:
            post = BlogPost.objects.get(slug=slug)
            post.is_published = False
            post.save()
            return Response({"detail": "Post unpublished."}, status=200)
        except BlogPost.DoesNotExist:
            return Response({"detail": "Post not found."}, status=404)


class BlogCategoryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlogCategorySerializer
    queryset = BlogCategory.objects.all()


class BlogCommentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlogCommentSerializer

    def perform_create(self, serializer):
        post = BlogPost.objects.get(
            slug=self.kwargs["slug"], is_published=True
        )
        serializer.save(post=post, author=self.request.user)