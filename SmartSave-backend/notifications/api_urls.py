from django.urls import path

from . import api_views

urlpatterns = [
    path("", api_views.NotificationListView.as_view(), name="notification-list"),
    # Static paths must come before <int:id> patterns
    path("read-all/", api_views.MarkAllReadView.as_view(), name="notification-read-all"),
    path("unread-count/", api_views.UnreadNotificationCountView.as_view(), name="notification-unread-count"),
    path("<int:id>/read/", api_views.MarkNotificationReadView.as_view(), name="notification-read"),
]
