from django.urls import path

from . import api_views

urlpatterns = [
    path("conversations/", api_views.ConversationListView.as_view(), name="conversation-list"),
    path("conversations/create/", api_views.CreateConversationView.as_view(), name="conversation-create"),
    path("conversations/<int:id>/", api_views.ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<int:id>/send/", api_views.SendMessageView.as_view(), name="conversation-send"),
    path("messages/<int:id>/read/", api_views.MarkAsReadView.as_view(), name="message-read"),
    path("unread-count/", api_views.UnreadCountView.as_view(), name="message-unread-count"),
]