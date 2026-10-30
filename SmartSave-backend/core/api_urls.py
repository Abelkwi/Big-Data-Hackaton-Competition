"""API URL Configuration: Routes all API endpoints under /api/."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("accounts.api_urls")),
    path("marketplace/", include("marketplace.api_urls")),
    path("orders/", include("orders.api_urls")),
    path("messaging/", include("messaging.api_urls")),
    path("notifications/", include("notifications.api_urls")),
    path("blog/", include("blog.api_urls")),
    path("innovation/", include("innovation.api_urls")),
    path("recovery/", include("recovery.api_urls")),
    path("contact/", include("contact.api_urls")),
    path("dashboard/", include("dashboard.api_urls")),
    path("accounts/", include("accounts.api_accounts_urls")),
    path("analytics/", include("analytics.api_urls")),
    path("home/", include("core.api_home_urls")),
]