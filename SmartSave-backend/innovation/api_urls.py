from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.InnovationIdeaListView.as_view(), name="innovation-list"),
    path("featured/", api_views.FeaturedIdeasView.as_view(), name="innovation-featured"),
    path("create/", api_views.InnovationIdeaCreateView.as_view(), name="innovation-create"),
    path("<slug:slug>/", api_views.InnovationIdeaDetailView.as_view(), name="innovation-detail"),
    path("<slug:slug>/vote/", api_views.ToggleVoteView.as_view(), name="innovation-vote"),
    path("<slug:slug>/comment/", api_views.AddCommentView.as_view(), name="innovation-comment"),
]