from django.urls import path

from . import api_views, admin_api_views, orders_api_views

urlpatterns = [
    path("farmer/", api_views.FarmerDashboardView.as_view(), name="dashboard-farmer"),
    path("buyer/", api_views.BuyerDashboardView.as_view(), name="dashboard-buyer"),
    path("ngo/", api_views.NGODashboardView.as_view(), name="dashboard-ngo"),
    path("admin/", admin_api_views.AdminOverviewView.as_view(), name="dashboard-admin"),
    path("admin/users/", admin_api_views.AdminUsersView.as_view(), name="dashboard-admin-users"),
    path("admin/users/<int:user_id>/", admin_api_views.AdminUserDetailView.as_view(), name="dashboard-admin-user-detail"),
    path("admin/users/<int:user_id>/verify/", admin_api_views.AdminUserVerificationView.as_view(), name="dashboard-admin-user-verify"),
    path("admin/users/<int:user_id>/activity/", admin_api_views.AdminUserActivityView.as_view(), name="dashboard-admin-user-activity"),
    path("admin/users/<int:user_id>/status/", admin_api_views.AdminUserStatusView.as_view(), name="dashboard-admin-user-status"),
    path("admin/activity/", admin_api_views.AdminActivityView.as_view(), name="dashboard-admin-activity"),
    path("admin/reports/", admin_api_views.AdminReportsView.as_view(), name="dashboard-admin-reports"),
    path("admin/reports/<int:report_id>/", admin_api_views.AdminReportsView.as_view(), name="dashboard-admin-report-detail"),
    path("reports/", admin_api_views.PublicReportCreateView.as_view(), name="moderation-report-create"),
    path("admin/health/", admin_api_views.AdminHealthView.as_view(), name="dashboard-admin-health"),
    path("admin/insights/reports/", admin_api_views.AdminInsightsReportView.as_view(), name="dashboard-admin-insights-reports"),
    path("admin/impact/", admin_api_views.AdminImpactView.as_view(), name="dashboard-admin-impact"),
    path("admin/settings/", admin_api_views.AdminSettingsView.as_view(), name="dashboard-admin-settings"),
    path("admin/orders/", orders_api_views.AdminOrdersView.as_view(), name="dashboard-admin-orders"),
    path("admin/moderation/", admin_api_views.AdminModerationView.as_view(), name="dashboard-admin-moderation-queue"),
    path("admin/announcements/", admin_api_views.AdminAnnouncementListView.as_view(), name="dashboard-admin-announcements"),
    path("admin/announcements/<int:announcement_id>/", admin_api_views.AdminAnnouncementDetailView.as_view(), name="dashboard-admin-announcement-detail"),
    path("announcements/", admin_api_views.PublicAnnouncementListView.as_view(), name="announcements-public"),
    path("admin/moderation/<str:item_type>/<int:item_id>/", admin_api_views.AdminModerationView.as_view(), name="dashboard-admin-moderation"),
]