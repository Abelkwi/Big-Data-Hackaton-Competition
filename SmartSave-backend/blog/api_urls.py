from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.BlogPostListView.as_view(), name="blog-list"),
    path("categories/", api_views.BlogCategoryListView.as_view(), name="blog-categories"),
    path("create/", api_views.BlogPostCreateView.as_view(), name="blog-create"),
    path("<slug:slug>/", api_views.BlogPostDetailView.as_view(), name="blog-detail"),
    path("<slug:slug>/update/", api_views.BlogPostUpdateView.as_view(), name="blog-update"),
    path("<slug:slug>/delete/", api_views.BlogPostDeleteView.as_view(), name="blog-delete"),
    path("<slug:slug>/comment/", api_views.BlogCommentCreateView.as_view(), name="blog-comment"),
]